"""系统声音采集：设备环回与按应用捕获（不静音其他应用）"""
import queue
import struct
import subprocess
import sys
import threading
import time

import pyaudiowpatch as pyaudio

from src.config import DEBUG_MODE, PROJECT_ROOT, load_settings, logger

# gummy-realtime-v1 要求 16kHz
SAMPLE_RATE = 16000
CHUNK_MS = 100
CHUNK_SAMPLES = SAMPLE_RATE * CHUNK_MS // 1000
CHUNK_BYTES = CHUNK_SAMPLES * 2


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


def _get_app_capture_exe_path() -> str | None:
    """返回 AppAudioCapture.exe 路径，未找到则返回 None。"""
    name = "AppAudioCapture.exe"
    candidates = [
        PROJECT_ROOT / name,
        PROJECT_ROOT / "tools" / "AppAudioCapture" / "bin" / "Release" / "net6.0" / "win-x64" / "publish" / name,
        PROJECT_ROOT / "tools" / "AppAudioCapture" / name,
    ]
    if getattr(sys, "frozen", False):
        candidates.insert(0, PROJECT_ROOT / name)
    for path in candidates:
        if path.exists():
            return str(path)
    return None


def _get_audio_sessions_for_exclude() -> list[dict]:
    """获取当前音频会话列表（用于 exclude 模式计算目标 PID）。"""
    if sys.platform != "win32":
        return []
    try:
        from pycaw.pycaw import AudioUtilities
        items = []
        seen = set()
        for session in AudioUtilities.GetAllSessions():
            if not session.Process:
                continue
            try:
                name = session.Process.name()
                pid = session.ProcessId
            except Exception:
                continue
            key = (pid, name)
            if key in seen:
                continue
            seen.add(key)
            items.append({"pid": pid, "name": name})
        return items
    except Exception:
        return []


def _target_pids_for_app_capture(mode: str, filter_items: list) -> list[int]:
    """根据 mode 与 filter_items 计算要传给外部工具的 PID 列表。include=要收录的 PID，exclude=要排除的 PID（工具仅取第一个）。"""
    pids = []
    for it in filter_items:
        try:
            if it.get("pid") is not None:
                pids.append(int(it["pid"]))
        except (TypeError, ValueError):
            pass
    return pids


def _capture_silence(
    audio_queue: queue.Queue,
    stop_event: threading.Event,
) -> None:
    """向 audio_queue 持续写入静音块，直到 stop_event。用于按应用模式下工具不可用时，避免误录其他应用。"""
    silent_chunk = bytes(CHUNK_BYTES)
    try:
        while not stop_event.is_set():
            try:
                audio_queue.put_nowait(silent_chunk)
            except queue.Full:
                pass
            stop_event.wait(CHUNK_MS / 1000.0)
    finally:
        try:
            audio_queue.put_nowait(None)
        except queue.Full:
            pass


def capture_apps(
    audio_queue: queue.Queue,
    stop_event: threading.Event,
    *,
    duration_sec: int | None = None,
) -> None:
    """
    通过外部工具按应用捕获（不静音其他应用）。若工具不可用或返回不支持，则回退为设备环回。
    duration_sec 非 None 时用于测试捕获，仅录制指定秒数。
    """
    settings = load_settings()
    mode = (settings.get("audio_filter_mode") or "all").lower()
    filter_items = settings.get("audio_filter_items") or []
    backend = (settings.get("audio_capture_backend") or "external_tool").strip().lower()
    denoise = bool(settings.get("audio_denoise_enabled", False))
    voice_enhance = bool(settings.get("audio_voice_enhance_enabled", False))

    if mode not in ("include", "exclude") or not filter_items:
        if logger:
            logger.info("按应用捕获: 模式或列表为空，使用设备环回")
        capture_loopback(audio_queue, stop_event)
        return

    pids = _target_pids_for_app_capture(mode, filter_items)
    if not pids:
        if logger:
            logger.warning("按应用捕获: 无有效目标进程，输出静音（不收录其他应用）")
        _capture_silence(audio_queue, stop_event)
        return

    exe_path = _get_app_capture_exe_path()
    if not exe_path or backend != "external_tool":
        if logger:
            logger.info("按应用捕获: 未找到 AppAudioCapture.exe 或后端非 external_tool，输出静音（不收录其他应用）")
        _capture_silence(audio_queue, stop_event)
        return

    args = [exe_path, "--mode", mode, "--pids", ",".join(str(p) for p in pids)]
    if duration_sec is not None:
        args.extend(["--duration", str(duration_sec)])

    if denoise or voice_enhance:
        from src.services.audio_processing import process_chunk as _process_chunk
    else:
        _process_chunk = None

    try:
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
    except Exception as e:
        if logger:
            logger.warning("按应用捕获: 启动辅助工具失败，输出静音（不收录其他应用）: %s", e)
        _capture_silence(audio_queue, stop_event)
        return

    time.sleep(0.3)
    if proc.poll() is not None:
        try:
            proc.wait(timeout=1)
        except Exception:
            pass
        if logger and proc.returncode == 2:
            logger.info("按应用捕获: 当前系统不支持进程环回，输出静音（不收录其他应用）")
        elif logger and proc.returncode != 0:
            logger.warning("按应用捕获: 辅助工具退出码 %s，输出静音", proc.returncode)
        _capture_silence(audio_queue, stop_event)
        return

    try:
        buf = bytearray()
        while not stop_event.is_set():
            try:
                chunk = proc.stdout.read(CHUNK_BYTES)
            except Exception:
                break
            if not chunk:
                break
            buf.extend(chunk)
            while len(buf) >= CHUNK_BYTES:
                out = bytes(buf[:CHUNK_BYTES])
                del buf[:CHUNK_BYTES]
                if _process_chunk:
                    out = _process_chunk(out, denoise=denoise, voice_enhance=voice_enhance)
                try:
                    audio_queue.put_nowait(out)
                except queue.Full:
                    pass
        try:
            audio_queue.put_nowait(None)
        except queue.Full:
            pass
    except Exception as e:
        if logger:
            logger.exception("按应用捕获异常: %s", e)
        try:
            audio_queue.put_nowait(None)
        except queue.Full:
            pass
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def capture_loopback(
    audio_queue: queue.Queue,
    stop_event: threading.Event,
) -> None:
    """
    在独立线程中捕获系统声音（设备环回，不修改任何应用音量），放入 audio_queue。
    放入 None 表示结束。
    """
    settings = load_settings()
    denoise = bool(settings.get("audio_denoise_enabled", False))
    voice_enhance = bool(settings.get("audio_voice_enhance_enabled", False))
    if denoise or voice_enhance:
        from src.services.audio_processing import process_chunk as _process_chunk

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
                        if denoise or voice_enhance:
                            out = _process_chunk(out, denoise=denoise, voice_enhance=voice_enhance)
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
