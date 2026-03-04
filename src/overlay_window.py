"""小窗显示：独立悬浮窗，按配置显示识别/翻译文字"""
import customtkinter as ctk

from src.config import load_settings
from src.pages.recognition_page import DisplayTarget


def _get_overlay_cfg():
    return (load_settings().get("overlay") or {}).copy()


def _screen_size(win: ctk.CTkBaseClass) -> tuple[int, int]:
    return win.winfo_screenwidth(), win.winfo_screenheight()


class OverlayDisplayTarget(DisplayTarget):
    """小窗用的 DisplayTarget，与主控制台同源数据、同逻辑"""

    def __init__(self, overlay_win: "OverlayWindow"):
        self._win = overlay_win
        self._finalized_content = ""
        self._streaming_recognition = ""
        self._streaming_translation = ""

    def append_text(self, text: str) -> None:
        self._win.append_text(text)

    def update_or_append(self, text: str, kind: str, sentence_end: bool) -> None:
        if kind == "recognition":
            self.update_batch(text, self._streaming_translation, sentence_end, False)
        else:
            self.update_batch(self._streaming_recognition, text, False, sentence_end)

    def _build_streaming_block(self) -> str:
        lines = []
        if self._streaming_recognition:
            lines.append(f"识别: {self._streaming_recognition}")
        if self._streaming_translation:
            lines.append(f"翻译: {self._streaming_translation}")
        return "\n".join(lines) + ("\n" if lines else "")

    def update_batch(self, recog_text: str, trans_text: str, recog_end: bool, trans_end: bool) -> None:
        if recog_text:
            self._streaming_recognition = recog_text
        if trans_text:
            self._streaming_translation = trans_text

        streaming = self._build_streaming_block()
        any_end = recog_end or trans_end
        if any_end:
            self._finalized_content += streaming
            self._streaming_recognition = ""
            self._streaming_translation = ""
            streaming = ""

        full = self._finalized_content + streaming
        self._win.set_content(full)

    def clear(self) -> None:
        self._finalized_content = ""
        self._streaming_recognition = ""
        self._streaming_translation = ""
        self._win.set_content("")


class OverlayWindow(ctk.CTkToplevel):
    """小窗：仅显示文字，大小/背景/字体等由配置控制；置顶、无标题栏、任意位置拖动"""

    def __init__(self, master):
        super().__init__(master)
        self.title("")
        self._drag_start_root_x = 0
        self._drag_start_root_y = 0
        self._drag_start_win_x = 0
        self._drag_start_win_y = 0

        self._textbox = ctk.CTkTextbox(
            self,
            wrap="word",
            border_width=0,
            fg_color="transparent",
        )
        self._textbox.pack(fill="both", expand=True, padx=8, pady=8)
        self._display_target = OverlayDisplayTarget(self)
        self.apply_config()

        # 强制置顶
        self.attributes("-topmost", True)
        # 去掉标题栏，任意位置可拖动
        self.overrideredirect(True)
        self._bind_drag()

    def _bind_drag(self):
        """在窗口和文本框上绑定：按下与拖动时移动窗口"""
        for w in (self, self._textbox):
            w.bind("<ButtonPress-1>", self._on_drag_start)
            w.bind("<B1-Motion>", self._on_drag_motion)

    def _on_drag_start(self, event):
        self._drag_start_root_x = event.x_root
        self._drag_start_root_y = event.y_root
        self._drag_start_win_x = self.winfo_x()
        self._drag_start_win_y = self.winfo_y()

    def _on_drag_motion(self, event):
        dx = event.x_root - self._drag_start_root_x
        dy = event.y_root - self._drag_start_root_y
        self.geometry(f"+{self._drag_start_win_x + dx}+{self._drag_start_win_y + dy}")

    def get_display_target(self) -> DisplayTarget:
        return self._display_target

    def apply_config(self):
        """从 config 重新读取并应用：尺寸、背景、透明度、字体、颜色、行距、对齐"""
        cfg = _get_overlay_cfg()
        sw, sh = _screen_size(self)
        w_pct = max(5, min(95, float(cfg.get("width_pct", 35))))
        h_pct = max(5, min(95, float(cfg.get("height_pct", 40))))
        w = int(sw * w_pct / 100)
        h = int(sh * h_pct / 100)
        self.geometry(f"{w}x{h}")
        self.minsize(120, 80)

        bg = str(cfg.get("bg_color", "#1a1a1a"))
        alpha = max(0.0, min(1.0, float(cfg.get("bg_alpha", 0.88))))
        self.configure(fg_color=bg)
        try:
            self.attributes("-alpha", alpha)
        except Exception:
            pass

        font_family = str(cfg.get("font_family", "Microsoft YaHei"))
        font_size = max(8, min(72, int(cfg.get("font_size", 16))))
        text_color = str(cfg.get("text_color", "#e5e5e5"))
        line_spacing = max(0, min(50, int(cfg.get("line_spacing", 8))))
        align = str(cfg.get("align", "left")).lower()
        if align not in ("left", "center", "right"):
            align = "left"

        self._textbox.configure(
            font=ctk.CTkFont(family=font_family, size=font_size),
            text_color=text_color,
        )
        try:
            self._textbox._textbox.configure(spacing1=line_spacing, spacing2=line_spacing, spacing3=line_spacing)
            self._textbox._textbox.tag_configure("all", justify=align)
        except Exception:
            pass
        # 保持置顶
        try:
            self.attributes("-topmost", True)
        except Exception:
            pass

    def set_content(self, text: str) -> None:
        def _do():
            self._textbox.delete("1.0", "end")
            if text:
                self._textbox.insert("1.0", text)
                try:
                    self._textbox._textbox.tag_add("all", "1.0", "end")
                except Exception:
                    pass
            self._textbox.see("end")

        self.after(0, _do)

    def append_text(self, text: str) -> None:
        def _do():
            self._textbox.insert("end", text)
            self._textbox.see("end")

        self.after(0, _do)
