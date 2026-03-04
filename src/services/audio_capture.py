"""系统声音采集（WASAPI 环回）"""
import queue
import struct
import threading

import pyaudiowpatch as pyaudio

from src.config import DEBUG_MODE, logger

# gummy-realtime-v1 要求 16kHz
SAMPLE_RATE = 16000
CHUNK_MS = 100
CHUNK_SAMPLES = SAMPLE_RATE * CHUNK_MS // 1000


def _resample_mono(raw: bytes, in_rate: int, in_channels: int) -> bytes:
    """将原始 PCM 转为 16kHz 单声道"""
    if in_channels == 1 and in_rate == SAMPLE_RATE:
        return raw
    samples = list(struct.unpack(f"<{len(raw)//2}h", raw))
    if in_channels == 2:
        samples = [(samples[i] + samples[i + 1]) // 2 for i in range(0, len(samples), 2)]
    if in_rate != SAMPLE_RATE:
        ratio = in_rate / SAMPLE_RATE
        new_len = int(len(samples) / ratio)
        indices = [min(int(i * ratio), len(samples) - 1) for i in range(new_len)]
        samples = [samples[i] for i in indices]
    return struct.pack(f"<{len(samples)}h", *samples)


def capture_loopback(
    audio_queue: queue.Queue,
    stop_event: threading.Event,
) -> None:
    """
    在独立线程中捕获系统声音，放入 audio_queue。
    放入 None 表示结束。
    """
    try:
        with pyaudio.PyAudio() as p:
            try:
                wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            except OSError:
                if logger:
                    logger.error("WASAPI 不可用")
                return
            default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
            if not default_speakers.get("isLoopbackDevice"):
                for loopback in p.get_loopback_device_info_generator():
                    if default_speakers["name"] in loopback["name"]:
                        default_speakers = loopback
                        break
                else:
                    if logger:
                        logger.error("未找到默认环回设备")
                    return
            dev_rate = int(default_speakers["defaultSampleRate"])
            dev_channels = default_speakers["maxInputChannels"]
            need_bytes = int(dev_rate * CHUNK_MS / 1000) * dev_channels * 2
            if logger:
                logger.info("音频采集: %s (%d Hz, %d ch)", default_speakers["name"], dev_rate, dev_channels)
            if DEBUG_MODE and logger:
                logger.debug("每块 %d 字节 -> 16kHz 单声道 %d 字节", need_bytes, CHUNK_SAMPLES * 2)
            buf_queue: queue.Queue = queue.Queue()

            def callback(in_data, frame_count, time_info, status):
                if status and logger:
                    logger.warning("音频状态: %s", status)
                buf_queue.put(in_data)
                return (in_data, pyaudio.paContinue)

            with p.open(
                format=pyaudio.paInt16,
                channels=dev_channels,
                rate=dev_rate,
                frames_per_buffer=1024,
                input=True,
                input_device_index=default_speakers["index"],
                stream_callback=callback,
            ) as stream:
                buf = bytearray()
                while not stop_event.is_set():
                    try:
                        buf.extend(buf_queue.get_nowait())
                    except queue.Empty:
                        pass
                    while len(buf) >= need_bytes:
                        chunk_raw = bytes(buf[:need_bytes])
                        del buf[:need_bytes]
                        out = _resample_mono(chunk_raw, dev_rate, dev_channels)
                        try:
                            audio_queue.put_nowait(out)
                        except queue.Full:
                            pass
                    stop_event.wait(0.02)
            try:
                audio_queue.put_nowait(None)
            except queue.Full:
                pass
    except Exception as e:
        if logger:
            logger.exception("音频采集异常: %s", e)
        try:
            audio_queue.put_nowait(None)
        except queue.Full:
            pass
