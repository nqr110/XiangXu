"""gummy-realtime-v1 WebSocket 客户端"""
import asyncio
import json
import queue
import ssl
import time
import uuid
from typing import Callable

import certifi
import websockets

from src.config import DEBUG_MODE, logger, load_settings

WS_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"
SAMPLE_RATE = 16000


def _ssl_context() -> ssl.SSLContext:
    """使用 certifi 的 CA 包创建 SSL 上下文，解决打包后无法验证证书的问题。"""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_verify_locations(certifi.where())
    return ctx


def _run_async(coro):
    """在新建事件循环中运行协程"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


_CONTINUE = object()


def _get_audio_chunk(audio_queue: queue.Queue, stop_check: Callable[[], bool]):
    """从 queue.Queue 获取下一块音频。返回 bytes|None(结束)|_CONTINUE(继续等待)"""
    if stop_check():
        return None
    try:
        return audio_queue.get(timeout=0.1)
    except queue.Empty:
        return _CONTINUE


async def _run_task_async(
    api_key: str,
    transcription_enabled: bool,
    translation_enabled: bool,
    source_language: str,
    translation_target_languages: list[str],
    audio_queue: queue.Queue,
    result_callback: Callable[[str, str, bool, bool], None],
    stop_check: Callable[[], bool],
):
    """异步执行单次任务"""
    task_id = uuid.uuid4().hex
    headers = {"Authorization": f"Bearer {api_key}"}

    run_task_msg = {
        "header": {"action": "run-task", "task_id": task_id, "streaming": "duplex"},
        "payload": {
            "model": "gummy-realtime-v1",
            "parameters": {
                "sample_rate": SAMPLE_RATE,
                "format": "pcm",
                "transcription_enabled": transcription_enabled,
                "translation_enabled": translation_enabled,
                "source_language": source_language,
                "translation_target_languages": translation_target_languages,
            },
            "input": {},
            "task": "asr",
            "task_group": "audio",
            "function": "recognition",
        },
    }

    if DEBUG_MODE and logger:
        logger.debug("run-task: %s", json.dumps(run_task_msg, ensure_ascii=False))

    if DEBUG_MODE and logger:
        logger.debug("连接 WebSocket: %s", WS_URL)

    # websockets 12+ 使用 additional_headers，旧版 (<12) 使用 extra_headers
    try:
        import inspect
        sig = inspect.signature(websockets.connect)
        use_additional = "additional_headers" in sig.parameters
    except Exception:
        use_additional = True
    connect_kw = {"additional_headers": headers} if use_additional else {"extra_headers": headers}
    connect_kw["ssl"] = _ssl_context()

    try:
        async with websockets.connect(WS_URL, **connect_kw) as ws:
            await ws.send(json.dumps(run_task_msg))
            task_started = False

            async def recv_loop():
                nonlocal task_started
                async for raw in ws:
                    if stop_check():
                        break
                    if isinstance(raw, bytes):
                        continue
                    try:
                        msg = json.loads(raw)
                        ev = msg.get("header", {}).get("event", "")
                        if ev == "task-started":
                            task_started = True
                            if DEBUG_MODE and logger:
                                logger.debug("收到 task-started")
                        elif ev == "result-generated":
                            out = msg.get("payload", {}).get("output", {})
                            trans = out.get("transcription") or {}
                            trans_text = (trans.get("text") or "").strip()
                            trans_end = trans.get("sentence_end", True)
                            trans_list = out.get("translations") or []
                            trans_tr = (trans_list[0].get("text") or "").strip() if trans_list else ""
                            tr_end = trans_list[0].get("sentence_end", True) if trans_list else True
                            recog = trans_text if transcription_enabled else ""
                            tr = trans_tr if translation_enabled else ""
                            recog_end = trans_end if transcription_enabled else False
                            tr_end_pass = tr_end if translation_enabled else False
                            if recog or tr:
                                result_callback(recog, tr, recog_end, tr_end_pass)
                            if DEBUG_MODE and logger and (trans_text or trans_tr):
                                logger.debug("result: 识别=%r (end=%s) 翻译=%r (end=%s)", trans_text, trans_end, trans_tr, tr_end)
                        elif ev == "task-finished":
                            if logger:
                                logger.info("服务端结束任务 (task-finished)，可能因长时间无语音超时，将自动重连")
                            break
                        elif ev == "task-failed":
                            err = msg.get("payload", {}).get("header", {})
                            if logger:
                                logger.error("task-failed: %s", err)
                            break
                    except json.JSONDecodeError:
                        pass
                    except Exception as e:
                        if logger:
                            logger.exception("解析消息异常: %s", e)

            recv_task = asyncio.create_task(recv_loop())
            try:
                while not task_started and not stop_check():
                    await asyncio.sleep(0.05)
                if stop_check():
                    return

                loop = asyncio.get_event_loop()
                while not stop_check():
                    chunk = await loop.run_in_executor(None, lambda: _get_audio_chunk(audio_queue, stop_check))
                    if chunk is _CONTINUE:
                        continue
                    if chunk is None:
                        break
                    await ws.send(chunk)
                    if DEBUG_MODE and logger:
                        logger.debug("发送音频块 %d 字节", len(chunk))

                finish_msg = {
                    "header": {"action": "finish-task", "task_id": task_id, "streaming": "duplex"},
                    "payload": {"input": {}},
                }
                await ws.send(json.dumps(finish_msg))
                if DEBUG_MODE and logger:
                    logger.debug("已发送 finish-task")

                await asyncio.wait_for(recv_task, timeout=10.0)
            except asyncio.TimeoutError:
                pass
            except Exception as e:
                if logger:
                    logger.exception("任务异常: %s", e)
            finally:
                recv_task.cancel()
                try:
                    await recv_task
                except asyncio.CancelledError:
                    pass
    except websockets.exceptions.InvalidStatusCode as e:
        if logger:
            logger.error("WebSocket 连接失败 (HTTP %s): %s", getattr(e, "status_code", ""), e)
    except Exception as e:
        if logger:
            logger.exception("WebSocket 异常: %s", e)


def run_realtime_session(
    transcription_enabled: bool,
    translation_enabled: bool,
    source_language: str,
    translation_target_languages: list[str],
    audio_queue: queue.Queue,
    result_callback: Callable[[str, str, bool, bool], None],
    stop_check: Callable[[], bool],
) -> None:
    """同步入口：在独立线程中运行异步任务。连接断开（如长时间无语音被服务端关闭）时会自动重连，直到用户点击停止。"""
    settings = load_settings()
    api_key = settings.get("api_key", "").strip()
    if not api_key:
        if logger:
            logger.error("未配置 API Key，请在设置页输入并保存")
        return
    if DEBUG_MODE and logger:
        logger.debug("gummy 会话启动: 识别=%s 翻译=%s 源语言=%s 目标语言=%s", transcription_enabled, translation_enabled, source_language, translation_target_languages)
    if not transcription_enabled and not translation_enabled:
        if logger:
            logger.error("至少需开启识别或翻译之一")
        return

    reconnect_delay_sec = 3
    run_count = 0
    while not stop_check():
        run_count += 1
        if logger and run_count > 1:
            logger.info("正在建立第 %d 次实时会话连接…", run_count)
        _run_async(
            _run_task_async(
                api_key=api_key,
                transcription_enabled=transcription_enabled,
                translation_enabled=translation_enabled,
                source_language=source_language,
                translation_target_languages=translation_target_languages,
                audio_queue=audio_queue,
                result_callback=result_callback,
                stop_check=stop_check,
            )
        )
        if stop_check():
            break
        if logger:
            logger.warning("实时会话已断开（可能因长时间无语音被服务端关闭），%s 秒后自动重连…", reconnect_delay_sec)
        for _ in range(reconnect_delay_sec * 10):
            if stop_check():
                return
            time.sleep(0.1)
