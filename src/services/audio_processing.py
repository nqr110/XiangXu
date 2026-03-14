"""实时音质处理：降噪（RNNoise）、人声增强（AGC）"""
import struct

from src.config import logger

# 与 audio_capture 一致：16kHz，100ms 块
SAMPLE_RATE_16K = 16000
CHUNK_SAMPLES_16K = 1600
RNNOISE_RATE = 48000
RNNOISE_FRAME = 480

_denoiser = None

def _get_denoiser():
    global _denoiser
    if _denoiser is None:
        try:
            from pyrnnoise import RNNoise
            _denoiser = RNNoise(sample_rate=RNNOISE_RATE)
        except Exception as e:
            if logger:
                logger.debug("pyrnnoise 不可用，降噪将跳过: %s", e)
    return _denoiser


def _resample_16k_to_48k(raw_16k: bytes) -> bytes:
    """1600 样本 16kHz -> 4800 样本 48kHz，线性插值"""
    n_in = len(raw_16k) // 2
    samples = list(struct.unpack(f"<{n_in}h", raw_16k))
    n_out = n_in * 3
    out = []
    for j in range(n_out):
        t = j / 3.0
        i0 = int(t)
        i1 = min(i0 + 1, n_in - 1)
        frac = t - i0
        v = samples[i0] * (1 - frac) + samples[i1] * frac
        out.append(max(-32768, min(32767, int(round(v)))))
    return struct.pack(f"<{len(out)}h", *out)


def _resample_48k_to_16k(raw_48k: bytes) -> bytes:
    """4800 样本 48kHz -> 1600 样本 16kHz"""
    n_in = len(raw_48k) // 2
    samples = list(struct.unpack(f"<{n_in}h", raw_48k))
    n_out = n_in // 3
    out = []
    for j in range(n_out):
        t = j * 3.0
        i0 = int(t)
        i1 = min(i0 + 1, n_in - 1)
        frac = t - i0
        v = samples[i0] * (1 - frac) + samples[i1] * frac
        out.append(max(-32768, min(32767, int(round(v)))))
    return struct.pack(f"<{len(out)}h", *out)


def _denoise_48k(raw_48k: bytes) -> bytes:
    """48kHz 16-bit mono 降噪，输入 4800 样本"""
    denoiser = _get_denoiser()
    if denoiser is None:
        return raw_48k
    try:
        import numpy as np
        arr = np.frombuffer(raw_48k, dtype=np.int16)
        arr = arr.reshape(1, -1)
        out_frames = []
        for _speech_prob, frame in denoiser.denoise_chunk(arr, partial=False):
            out_frames.append(frame)
        if not out_frames:
            return raw_48k
        out_arr = np.concatenate(out_frames, axis=1)
        return out_arr.astype(np.int16).tobytes()
    except Exception as e:
        if logger:
            logger.debug("降噪处理异常: %s", e)
        return raw_48k


def _voice_enhance_agc(raw_16k: bytes, target_rms: int = 2000, max_gain: float = 4.0) -> bytes:
    """按块 AGC：将块内 RMS 归一到 target_rms，增益上限 max_gain"""
    n = len(raw_16k) // 2
    if n == 0:
        return raw_16k
    samples = list(struct.unpack(f"<{n}h", raw_16k))
    rms = (sum(s * s for s in samples) / n) ** 0.5
    if rms <= 0:
        return raw_16k
    gain = target_rms / rms
    if gain > max_gain:
        gain = max_gain
    out = [max(-32768, min(32767, int(round(s * gain)))) for s in samples]
    return struct.pack(f"<{len(out)}h", *out)


def process_chunk(
    raw_16k: bytes,
    denoise: bool,
    voice_enhance: bool,
) -> bytes:
    """
    对单块 16kHz 16-bit 单声道 PCM 做可选降噪与人声增强。
    输入/输出长度一致（与 audio_capture.CHUNK_SAMPLES 对应）。
    """
    if not denoise and not voice_enhance:
        return raw_16k
    out = raw_16k
    if denoise:
        up = _resample_16k_to_48k(out)
        up = _denoise_48k(up)
        out = _resample_48k_to_16k(up)
    if voice_enhance:
        out = _voice_enhance_agc(out)
    return out
