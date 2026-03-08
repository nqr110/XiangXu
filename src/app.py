"""主窗口与导航框架"""
import json
import os
import sys
import queue
import tempfile
import threading
from pathlib import Path

import customtkinter as ctk

from src.config import (
    CONSOLE_HEIGHT,
    CONSOLE_MIN_HEIGHT,
    CONSOLE_MIN_WIDTH,
    CONSOLE_WIDTH,
    PROJECT_ROOT,
    RESOURCES_DIR,
    load_settings,
    logger,
)

# #region agent log
def _debug_log(location: str, message: str, data: dict, hypothesis_id: str):
    try:
        log_path = PROJECT_ROOT / "debug-21d81f.log"
        payload = {"sessionId": "21d81f", "location": location, "message": message, "data": data, "hypothesisId": hypothesis_id, "timestamp": __import__("time").time() * 1000}
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
# #endregion
from src.pages.overlay_page import OverlayPage
from src.pages.recognition_page import RecognitionPage
from src.pages.settings_page import SettingsPage
from src.pages.suggestion_page import SuggestionPage
from src.overlay_window import OverlayWindow
from src.services.audio_capture import capture_loopback
from src.services.gummy_client import run_realtime_session
from src.theme import (
    ACCENT,
    BG_MAIN,
    BG_NAV,
    BORDER_COLOR,
    BTN_RADIUS,
    BTN_SECONDARY_HOVER,
    NAV_ACTIVE_FG,
    NAV_ACTIVE_TEXT,
    TEXT_BODY,
)

# 浅色主题
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# DPI：默认开启 DPI 感知以在高分屏下获得清晰圆角与边框。仅当出现双屏/多屏拖拽导致的
# TclError 或主窗口透明度异常时，在 .env 或环境中设置 CTK_DEACTIVATE_DPI=1 再关闭（会牺牲清晰度）。
if os.getenv("CTK_DEACTIVATE_DPI", "").strip().lower() in ("1", "true", "yes"):
    ctk.deactivate_automatic_dpi_awareness()

# 圆角绘制方式：默认 font_shapes 以使用抗锯齿圆角，减轻钝齿/毛刺。若环境存在字体或渲染异常，
# 可设置 CTK_DRAW_METHOD=circle_shapes 或 polygon_shapes 回退。
_draw_method = (os.getenv("CTK_DRAW_METHOD", "font_shapes") or "font_shapes").strip().lower()
if _draw_method not in ("font_shapes", "circle_shapes", "polygon_shapes"):
    _draw_method = "font_shapes"
try:
    ctk.DrawEngine.preferred_drawing_method = _draw_method
except Exception:
    ctk.DrawEngine.preferred_drawing_method = "circle_shapes"
    if logger:
        logger.warning("CTK_DRAW_METHOD=%s 设置失败，已回退为 circle_shapes", _draw_method)


class App(ctk.CTk):
    """主应用窗口"""

    def __init__(self):
        super().__init__()
        self.title("象胥")
        settings = load_settings()
        # 启动宽高：优先 config.json（用户曾在设置页保存），否则 .env；且不小于 .env 中的最小宽高
        w = max(CONSOLE_MIN_WIDTH, int(settings.get("console_width") or CONSOLE_WIDTH))
        h = max(CONSOLE_MIN_HEIGHT, int(settings.get("console_height") or CONSOLE_HEIGHT))
        self.geometry(f"{w}x{h}")
        self.minsize(CONSOLE_MIN_WIDTH, CONSOLE_MIN_HEIGHT)
        self.configure(fg_color=BG_MAIN)

        self._recognition_page: RecognitionPage | None = None
        self._current_page: ctk.CTkFrame | None = None
        self._current_nav_key: str = ""
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._nav_indicators: dict[str, ctk.CTkFrame] = {}
        self._nav_left_cover: dict[str, ctk.CTkFrame] = {}
        self._pages: dict[str, ctk.CTkFrame] = {}
        self._overlay_window: OverlayWindow | None = None
        self._overlay_display_target = None  # DisplayTarget from overlay
        self._stop_event: threading.Event | None = None
        self._audio_queue: queue.Queue | None = None
        self._audio_thread: threading.Thread | None = None
        self._gummy_thread: threading.Thread | None = None

        self._build_ui()
        self._wire_recognition()
        # 主窗口始终不透明，防止跨屏 DPI 异常后误被设为半透明
        self._ensure_main_window_opaque()
        # 获得焦点时置前，避免被游戏全屏无边框窗口抢走后无法恢复
        self._bind_focus_lift()

    def _build_ui(self):
        # 左侧导航栏：靠左列表样式，独立背景色
        nav = ctk.CTkFrame(
            self,
            width=172,
            fg_color=BG_NAV,
            corner_radius=0,
            border_width=0,
        )
        nav.pack(side="left", fill="y", padx=(0, 0), pady=0)
        nav.pack_propagate(False)
        nav_inner = ctk.CTkFrame(nav, fg_color="transparent")
        nav_inner.pack(side="top", fill="x", expand=False, padx=12, pady=(12, 12))

        logo_path = RESOURCES_DIR / "images" / "logo.jpg"
        # #region agent log
        _debug_log("app.py:logo_path", "logo path resolution", {"project_root": str(PROJECT_ROOT), "logo_path": str(logo_path), "exists": logo_path.exists()}, "H1")
        # #endregion
        # Logo
        if logo_path.exists():
            try:
                logo_img = ctk.CTkImage(light_image=str(logo_path), dark_image=str(logo_path), size=(140, 140))
                logo_label = ctk.CTkLabel(nav_inner, image=logo_img, text="")
                logo_label.pack(pady=(0, 12))
            except Exception:
                try:
                    from PIL import Image
                    img = Image.open(logo_path).convert("RGB")
                    fd, path = tempfile.mkstemp(suffix=".png")
                    os.close(fd)
                    img.save(path)
                    logo_img = ctk.CTkImage(light_image=path, dark_image=path, size=(140, 140))
                    logo_label = ctk.CTkLabel(nav_inner, image=logo_img, text="")
                    logo_label.pack(pady=(0, 12))
                except Exception:
                    pass

        nav_items = [
            ("识别与翻译", "recognition"),
            ("对话建议", "suggestion"),
            ("小窗显示", "overlay"),
            ("设置", "settings"),
        ]
        nav_font = ctk.CTkFont(size=14)
        for text, key in nav_items:
            row = ctk.CTkFrame(nav_inner, fg_color="transparent", height=40)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)
            ind = ctk.CTkFrame(row, width=3, fg_color="transparent", corner_radius=0)
            ind.pack(side="left", fill="y")
            self._nav_indicators[key] = ind
            # 容器：先放圆角按钮，再在左侧叠一层直角遮罩，实现「左直角、右圆角」
            nav_btn_wrapper = ctk.CTkFrame(row, fg_color="transparent")
            nav_btn_wrapper.pack(side="left", fill="both", expand=True)
            btn = ctk.CTkButton(
                nav_btn_wrapper,
                text=text,
                command=lambda k=key: self._show_page(k),
                anchor="w",
                fg_color="transparent",
                text_color=(TEXT_BODY, "gray90"),
                hover_color=(BTN_SECONDARY_HOVER, "#3a3a3a"),
                corner_radius=BTN_RADIUS,
                height=40,
                font=nav_font,
            )
            btn.pack(fill="both", expand=True)
            self._nav_buttons[key] = btn
            left_cover = ctk.CTkFrame(
                nav_btn_wrapper, width=BTN_RADIUS, fg_color=BG_NAV, corner_radius=0
            )
            left_cover.place(x=0, rely=0, relheight=1)
            self._nav_left_cover[key] = left_cover

        # 导航与内容区之间的分界线
        sep = ctk.CTkFrame(self, width=2, fg_color=BORDER_COLOR, corner_radius=0)
        sep.pack(side="left", fill="y", padx=0, pady=0)
        sep.pack_propagate(False)

        # 右侧内容区（与主背景一致，避免遮罩移除时色差）
        self.content = ctk.CTkFrame(self, fg_color=BG_MAIN)
        self.content.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # 创建各页面，叠放在同一 grid 格内
        self._recognition_page = RecognitionPage(self.content, on_start=None, on_stop=None)
        self._pages["recognition"] = self._recognition_page
        self._pages["suggestion"] = SuggestionPage(self.content)
        self._overlay_page = OverlayPage(
            self.content,
            on_open_overlay=self._open_overlay,
            on_close_overlay=self._close_overlay,
            is_overlay_open=self._is_overlay_open,
            on_apply_config=self._apply_overlay_config,
            on_lock_overlay=self._set_overlay_lock,
        )
        self._pages["overlay"] = self._overlay_page
        self._pages["settings"] = SettingsPage(
            self.content,
            on_apply_console_size=self._apply_console_size,
        )
        for page in self._pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        # 切换遮罩：与主背景同色，切换时盖住内容区，在背后完成 tkraise 与重绘后降下，消除「从上到下」刷新感
        self._switch_cover = ctk.CTkFrame(
            self.content,
            fg_color=BG_MAIN,
            corner_radius=0,
            border_width=0,
        )
        self._switch_cover.grid(row=0, column=0, sticky="nsew")
        self._switch_cover.lower()  # 初始在所有页面之下

        self._show_page("recognition")  # 会同时高亮导航并 tkraise 识别页

        # 窗口图标（使用 images/logo.jpg，需 Pillow 支持 jpg）
        self._set_window_icon(logo_path if logo_path.exists() else None)

    def _show_page(self, key: str):
        self._current_nav_key = key
        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(fg_color=NAV_ACTIVE_FG, text_color=NAV_ACTIVE_TEXT)
            else:
                btn.configure(fg_color="transparent", text_color=(TEXT_BODY, "gray90"))
        for k, ind in self._nav_indicators.items():
            ind.configure(fg_color=ACCENT if k == key else "transparent")
        for k, left_cover in self._nav_left_cover.items():
            left_cover.configure(fg_color=NAV_ACTIVE_FG if k == key else BG_NAV)

        # 遮罩盖住内容区 → 背后切换并重绘 → 降下遮罩，避免从上到下的刷新闪烁
        self._switch_cover.tkraise()
        self.content.update_idletasks()
        self._pages[key].tkraise()
        self.content.update_idletasks()
        self._switch_cover.lower(self._pages[key])

        self._current_page = self._pages[key]
        if key == "overlay" and hasattr(self._current_page, "refresh_toggle_button"):
            self._current_page.refresh_toggle_button()

    def _is_overlay_open(self) -> bool:
        if not self._overlay_window:
            return False
        try:
            return self._overlay_window.winfo_exists()
        except Exception:
            return False

    def _open_overlay(self):
        if self._overlay_window and self._overlay_window.winfo_exists():
            self._overlay_window.focus()
            return
        self._overlay_window = OverlayWindow(self)
        self._overlay_display_target = self._overlay_window.get_display_target()

        def on_close():
            self._overlay_window = None
            self._overlay_display_target = None
            if self._overlay_page and self._overlay_page.winfo_exists():
                self._overlay_page.set_overlay_open(False)

        self._overlay_window.protocol("WM_DELETE_WINDOW", on_close)
        self._overlay_page.set_overlay_open(True)
        self._overlay_page.set_overlay_locked(False)

    def _close_overlay(self):
        if self._overlay_window and self._overlay_window.winfo_exists():
            self._overlay_window.destroy()
        self._overlay_window = None
        self._overlay_display_target = None
        if self._overlay_page and self._overlay_page.winfo_exists():
            self._overlay_page.set_overlay_open(False)

    def _apply_overlay_config(self):
        if self._overlay_window and self._overlay_window.winfo_exists():
            self._overlay_window.apply_config()

    def _set_overlay_lock(self, locked: bool) -> None:
        """设置小窗是否锁定（鼠标穿透），供小窗页「窗口锁定」按钮调用。"""
        if self._overlay_window and self._overlay_window.winfo_exists():
            self._overlay_window.set_mouse_passthrough(locked)

    def _set_window_icon(self, logo_path: Path | None):
        if not logo_path:
            return
        # #region agent log
        _debug_log("app.py:_set_window_icon", "entry", {"logo_path": str(logo_path)}, "H2")
        # #endregion
        try:
            from PIL import Image
            from PIL.ImageTk import PhotoImage

            img = Image.open(logo_path).convert("RGB")
            if sys.platform.startswith("win"):
                # Windows 上 CustomTkinter 在 200ms 时用 iconbitmap(.ico) 覆盖图标；只有调用 iconbitmap 才会置 _iconbitmap_method_called，
                # CTk 才不再覆盖。故用 logo 生成临时 .ico 并调用 iconbitmap。
                fd, ico_path = tempfile.mkstemp(suffix=".ico")
                os.close(fd)
                try:
                    # 多档尺寸供 Windows/高 DPI 选用，避免放大小图导致模糊
                    img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
                    self.iconbitmap(ico_path)
                    self._icon_ico_path = ico_path
                except Exception:
                    try:
                        os.unlink(ico_path)
                    except OSError:
                        pass
                    raise
                # #region agent log
                _debug_log("app.py:_set_window_icon", "iconbitmap(ico) called", {"ico_path": ico_path}, "H2")
                # #endregion
            else:
                self._icon_photo = PhotoImage(img)
                self.after(0, lambda: self.iconphoto(True, self._icon_photo))
                # #region agent log
                _debug_log("app.py:_set_window_icon", "iconphoto (non-Windows)", {}, "H2")
                # #endregion
        except Exception as e:
            # #region agent log
            _debug_log("app.py:_set_window_icon", "exception", {"error": str(e), "error_type": type(e).__name__}, "H2")
            # #endregion
            if isinstance(e, ModuleNotFoundError) and e.name == "PIL":
                if logger:
                    logger.warning("未安装 Pillow，无法设置窗口图标。请使用项目 .venv 并执行: pip install -r requirements.txt")
            pass

    def _apply_console_size(self, width: int, height: int):
        """应用控制台窗口尺寸（由设置页保存时调用）"""
        try:
            if self.winfo_exists():
                self.geometry(f"{width}x{height}")
        except Exception:
            pass

    def _ensure_main_window_opaque(self):
        """保证主窗口始终不透明，避免双屏拖拽触发的 DPI 缩放异常导致窗口变透明"""
        self.attributes("-alpha", 1.0)

        def _on_configure(_event=None):
            try:
                if self.winfo_exists():
                    self.attributes("-alpha", 1.0)
            except Exception:
                pass

        self.bind("<Configure>", _on_configure, add=True)

    def _bind_focus_lift(self):
        """获得焦点时将主窗口提到最前，避免被游戏全屏无边框窗口盖住后难以恢复。仅当焦点落在主窗口本身上时才 focus_set，否则会抢走输入框等子控件焦点导致无法输入。"""
        def _on_focus_in(event=None):
            try:
                if not self.winfo_exists():
                    return
                self.lift()
                # 仅当焦点目标为主窗口时才 focus_set，避免从输入框等子控件抢走焦点
                if event and getattr(event, "widget", None) == self:
                    self.focus_set()
            except Exception:
                pass
        self.bind("<FocusIn>", _on_focus_in, add=True)

    def _wire_recognition(self):
        """将识别页与 gummy_client、audio_capture 联动"""
        if not self._recognition_page:
            return
        display = self._recognition_page.get_display_target()

        def on_start(transcription_enabled: bool, translation_enabled: bool):
            settings = load_settings()
            if not (settings.get("api_key") or "").strip():
                if logger:
                    logger.error("未配置 API Key，请先在设置页输入并保存")
                self._recognition_page.set_running(False)
                return
            self._stop_event = threading.Event()
            self._audio_queue = queue.Queue(maxsize=100)
            source_lang = settings.get("source_language", "en")
            target_langs = settings.get("translation_target_languages", ["zh"])
            if logger:
                logger.info("启动识别与翻译: 识别=%s 翻译=%s", transcription_enabled, translation_enabled)

            def result_cb(recog_text: str, trans_text: str, recog_end: bool, trans_end: bool):
                if not display or (not recog_text and not trans_text):
                    return
                def _update(r, t, re, te):
                    display.update_batch(r, t, re, te)
                    if self._overlay_display_target:
                        self._overlay_display_target.update_batch(r, t, re, te)
                self.after(0, lambda: _update(recog_text, trans_text, recog_end, trans_end))

            def stop_check():
                return self._stop_event.is_set() if self._stop_event else True

            self._audio_thread = threading.Thread(
                target=capture_loopback,
                args=(self._audio_queue, self._stop_event),
                daemon=True,
            )
            self._audio_thread.start()

            self._gummy_thread = threading.Thread(
                target=run_realtime_session,
                args=(
                    transcription_enabled,
                    translation_enabled,
                    source_lang,
                    target_langs,
                    self._audio_queue,
                    result_cb,
                    stop_check,
                ),
                daemon=True,
            )
            self._gummy_thread.start()
            self._recognition_page.set_running(True)

        def on_stop():
            if self._stop_event:
                self._stop_event.set()
            if self._audio_queue:
                try:
                    self._audio_queue.put_nowait(None)
                except queue.Full:
                    pass

        self._recognition_page.set_callbacks(on_start, on_stop)

    def get_recognition_page(self) -> RecognitionPage | None:
        return self._recognition_page
