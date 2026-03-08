"""小窗显示：独立悬浮窗，按配置显示识别/翻译文字"""
import sys
import customtkinter as ctk

from src.config import load_settings, save_settings
from src.pages.recognition_page import DisplayTarget


def _get_overlay_cfg():
    return (load_settings().get("overlay") or {}).copy()


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """将 #rgb 或 #rrggbb 转为 (r,g,b) 0-255"""
    s = (hex_str or "").strip().lstrip("#")
    if len(s) == 3:
        s = s[0] * 2 + s[1] * 2 + s[2] * 2
    if len(s) != 6:
        return (0, 0, 0)
    try:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    except ValueError:
        return (0, 0, 0)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"


def _blend_hex(bg_hex: str, text_hex: str, text_alpha: float) -> str:
    """按 text_alpha 将文字颜色与背景色混合，模拟文字透明度。1=纯文字色，0=与背景同色。"""
    t = max(0.0, min(1.0, float(text_alpha)))
    br, bg, bb = _hex_to_rgb(bg_hex)
    tr, tg, tb = _hex_to_rgb(text_hex)
    r = int((1 - t) * br + t * tr)
    g = int((1 - t) * bg + t * tg)
    b = int((1 - t) * bb + t * tb)
    return _rgb_to_hex(r, g, b)


def _screen_size(win: ctk.CTkBaseClass) -> tuple[int, int]:
    return win.winfo_screenwidth(), win.winfo_screenheight()


# 用于 -transparentcolor 的占位色（圆角时窗口四角为此色并设为透明，仅 CTkFrame 负责绘制圆角）
_OVERLAY_TRANSPARENT_COLOR = "#010102"


class OverlayDisplayTarget(DisplayTarget):
    """小窗用的 DisplayTarget，与主控制台同源数据、同逻辑；支持简洁模式与拆分字幕"""

    def __init__(self, overlay_win: "OverlayWindow"):
        self._win = overlay_win
        self._finalized_segments: list[tuple[str, str]] = []  # (text, "recognition"|"translation")
        self._streaming_recognition = ""
        self._streaming_translation = ""

    def append_text(self, text: str) -> None:
        self._win.append_text(text)

    def update_or_append(self, text: str, kind: str, sentence_end: bool) -> None:
        if kind == "recognition":
            self.update_batch(text, self._streaming_translation, sentence_end, False)
        else:
            self.update_batch(self._streaming_recognition, text, False, sentence_end)

    def _format_line(self, text: str, kind: str, simple_mode: bool) -> str:
        if not text.strip():
            return ""
        if simple_mode:
            return text
        return f"识别: {text}" if kind == "recognition" else f"翻译: {text}"

    def _build_display(self) -> tuple[str, list[str] | None]:
        """返回 (全文, 每行对齐方式列表或 None)。拆分模式下为 "left"/"right"。"""
        cfg = _get_overlay_cfg()
        simple_mode = cfg.get("simple_mode", False)
        split_mode = cfg.get("split_subtitle_mode", False)
        lines: list[str] = []
        line_kinds: list[str] = []  # "recognition"|"translation" 与 lines 一一对应

        for text, kind in self._finalized_segments:
            line = self._format_line(text, kind, simple_mode)
            if line:
                lines.append(line)
                line_kinds.append(kind)
        if self._streaming_recognition:
            line = self._format_line(self._streaming_recognition, "recognition", simple_mode)
            if line:
                lines.append(line)
                line_kinds.append("recognition")
        if self._streaming_translation:
            line = self._format_line(self._streaming_translation, "translation", simple_mode)
            if line:
                lines.append(line)
                line_kinds.append("translation")

        alignments: list[str] | None = None
        if split_mode and lines:
            has_rec = "recognition" in line_kinds
            has_trans = "translation" in line_kinds
            if has_rec and has_trans:
                alignments = ["left" if k == "recognition" else "right" for k in line_kinds]
            else:
                alignments = ["left" if i % 2 == 0 else "right" for i in range(len(lines))]

        full = "\n".join(lines)
        return full, alignments

    def update_batch(self, recog_text: str, trans_text: str, recog_end: bool, trans_end: bool) -> None:
        if recog_text:
            self._streaming_recognition = recog_text
        if trans_text:
            self._streaming_translation = trans_text

        any_end = recog_end or trans_end
        if any_end:
            if self._streaming_recognition:
                self._finalized_segments.append((self._streaming_recognition, "recognition"))
            if self._streaming_translation:
                self._finalized_segments.append((self._streaming_translation, "translation"))
            self._streaming_recognition = ""
            self._streaming_translation = ""

        full, line_alignments = self._build_display()
        self._win.set_content(full, line_alignments=line_alignments)

    def clear(self) -> None:
        self._finalized_segments.clear()
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

        # 内层全屏 Frame：CTkToplevel 在 overrideredirect 下圆角不生效，由 Frame 绘制圆角
        self._inner_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            border_width=0,
        )
        self._inner_frame.pack(fill="both", expand=True)

        self._textbox = ctk.CTkTextbox(
            self._inner_frame,
            wrap="word",
            border_width=0,
            fg_color="transparent",
            activate_scrollbars=False,
        )
        self._textbox.pack(fill="both", expand=True, padx=8, pady=8)
        self._bind_mousewheel_scroll()
        # 小窗仅用于展示识别/翻译结果，禁止用户输入
        self._set_textbox_readonly(True)
        self._display_target = OverlayDisplayTarget(self)
        self.apply_config()

        # 强制置顶
        self.attributes("-topmost", True)
        # 去掉标题栏，任意位置可拖动
        self.overrideredirect(True)
        self._bind_drag()
        # 定时重新应用置顶，防止被游戏全屏无边框窗口覆盖后失效
        self._schedule_topmost_refresh()

    def _set_textbox_readonly(self, readonly: bool):
        """设置文本框只读（不可编辑）或可编辑。小窗仅展示用，应保持只读。"""
        try:
            self._textbox._textbox.configure(state="disabled" if readonly else "normal")
        except Exception:
            pass

    def _bind_mousewheel_scroll(self):
        """无滚动条时仍可用鼠标滚轮上下翻页"""
        def _on_wheel(event):
            try:
                tb = self._textbox._textbox
                delta = -1 * (event.delta // 120) if event.delta else 0
                if delta:
                    tb.yview_scroll(delta, "units")
            except Exception:
                pass
        self._textbox.bind("<MouseWheel>", _on_wheel)
        self._textbox._textbox.bind("<MouseWheel>", _on_wheel)

    def _schedule_topmost_refresh(self):
        """每隔一段时间重新应用置顶，避免被全屏/无边框游戏窗口抢走 Z-order"""
        def _refresh():
            try:
                if self.winfo_exists():
                    self.attributes("-topmost", True)
                    self.after(2000, _refresh)
            except Exception:
                pass
        self.after(2000, _refresh)

    def _bind_drag(self):
        """在窗口、内层框架和文本框上绑定：按下与拖动时移动窗口；松开时保存位置"""
        for w in (self, self._inner_frame, self._textbox):
            w.bind("<ButtonPress-1>", self._on_drag_start)
            w.bind("<B1-Motion>", self._on_drag_motion)
            w.bind("<ButtonRelease-1>", self._on_drag_release)

    def _on_drag_start(self, event):
        self._drag_start_root_x = event.x_root
        self._drag_start_root_y = event.y_root
        self._drag_start_win_x = self.winfo_x()
        self._drag_start_win_y = self.winfo_y()

    def _on_drag_motion(self, event):
        dx = event.x_root - self._drag_start_root_x
        dy = event.y_root - self._drag_start_root_y
        self.geometry(f"+{self._drag_start_win_x + dx}+{self._drag_start_win_y + dy}")

    def _on_drag_release(self, event):
        self.after(50, self._save_position)

    def _save_position(self) -> None:
        """将当前小窗位置以相对位置（百分比）写入 config.json，适配不同分辨率"""
        try:
            if not self.winfo_exists():
                return
            sw, sh = _screen_size(self)
            w = self.winfo_width()
            h = self.winfo_height()
            x = self.winfo_x()
            y = self.winfo_y()
            range_x = max(1, sw - w)
            range_y = max(1, sh - h)
            x_pct = max(0.0, min(100.0, 100.0 * x / range_x))
            y_pct = max(0.0, min(100.0, 100.0 * y / range_y))
            settings = load_settings()
            overlay = settings.get("overlay") or {}
            overlay["position_x_pct"] = round(x_pct, 2)
            overlay["position_y_pct"] = round(y_pct, 2)
            overlay.pop("position_x", None)
            overlay.pop("position_y", None)
            settings["overlay"] = overlay
            save_settings(settings)
        except Exception:
            pass

    def get_display_target(self) -> DisplayTarget:
        return self._display_target

    def _set_mouse_passthrough(self, enabled: bool) -> None:
        """Windows 下设置窗口鼠标穿透（WS_EX_TRANSPARENT），非 Windows 无操作。"""
        if sys.platform != "win32":
            return
        try:
            self.update_idletasks()
            hwnd = self.winfo_id()
            if not hwnd:
                return
            # Tk 的 Toplevel 在 Windows 上 winfo_id() 可能返回子控件，需取到顶层 HWND
            try:
                user32 = __import__("ctypes").windll.user32
            except Exception:
                return
            GWL_EXSTYLE = -20
            WS_EX_TRANSPARENT = 0x00000020
            parent = user32.GetParent(hwnd)
            target_hwnd = parent if parent else hwnd
            ex_style = user32.GetWindowLongW(target_hwnd, GWL_EXSTYLE)
            if enabled:
                ex_style |= WS_EX_TRANSPARENT
            else:
                ex_style &= ~WS_EX_TRANSPARENT
            user32.SetWindowLongW(target_hwnd, GWL_EXSTYLE, ex_style)
        except Exception:
            pass

    def set_mouse_passthrough(self, enabled: bool) -> None:
        """设置鼠标是否穿透小窗（锁定后 enabled=True，游戏时避免误触）。"""
        self._set_mouse_passthrough(enabled)

    def apply_config(self):
        """从 config 重新读取并应用：尺寸、背景、透明度、字体、颜色、行距、对齐"""
        cfg = _get_overlay_cfg()
        sw, sh = _screen_size(self)
        w_pct = max(5, min(95, float(cfg.get("width_pct", 35))))
        h_pct = max(5, min(95, float(cfg.get("height_pct", 40))))
        w = int(sw * w_pct / 100)
        h = int(sh * h_pct / 100)
        def_x = (sw - w) // 2
        def_y = (sh - h) // 2
        margin = 50
        try:
            px_pct = cfg.get("position_x_pct")
            py_pct = cfg.get("position_y_pct")
            if px_pct is not None and py_pct is not None:
                px = max(0.0, min(100.0, float(px_pct)))
                py = max(0.0, min(100.0, float(py_pct)))
                range_x = max(0, sw - w)
                range_y = max(0, sh - h)
                x = int(range_x * px / 100) if range_x else 0
                y = int(range_y * py / 100) if range_y else 0
            else:
                # 兼容旧配置：仅有 position_x/position_y 时按像素使用
                px_abs = cfg.get("position_x")
                py_abs = cfg.get("position_y")
                if px_abs is not None and py_abs is not None:
                    x = int(float(px_abs))
                    y = int(float(py_abs))
                    x = max(-w + margin, min(sw - margin, x))
                    y = max(-h + margin, min(sh - margin, y))
                else:
                    x, y = def_x, def_y
        except (TypeError, ValueError):
            x, y = def_x, def_y
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(120, 80)

        bg = str(cfg.get("bg_color", "#1a1a1a"))
        bg_alpha = max(0.0, min(1.0, float(cfg.get("bg_alpha", 0.88))))
        corner_style = str(cfg.get("corner_style", "rounded")).lower()
        corner_radius_val = max(0, min(80, int(cfg.get("corner_radius", 12))))
        corner_radius = 0 if corner_style == "square" else corner_radius_val
        # 圆角：Toplevel 用透明占位色，内层 Frame 绘制圆角；直角：Toplevel 与 Frame 同色
        if corner_radius > 0:
            self.configure(fg_color=_OVERLAY_TRANSPARENT_COLOR)
            self._inner_frame.configure(fg_color=bg, corner_radius=corner_radius)
            try:
                self.attributes("-transparentcolor", _OVERLAY_TRANSPARENT_COLOR)
            except Exception:
                pass
        else:
            self.configure(fg_color=bg)
            self._inner_frame.configure(fg_color=bg, corner_radius=0)
            try:
                self.attributes("-transparentcolor", "")
            except Exception:
                pass
        try:
            self.attributes("-alpha", bg_alpha)
        except Exception:
            pass

        font_family = str(cfg.get("font_family", "Microsoft YaHei"))
        font_size = max(8, min(72, int(cfg.get("font_size", 16))))
        text_color_raw = str(cfg.get("text_color", "#e5e5e5"))
        text_alpha = max(0.0, min(1.0, float(cfg.get("text_alpha", 1.0))))
        text_color = _blend_hex(bg, text_color_raw, text_alpha)
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
            self._textbox._textbox.tag_configure("align_left", justify="left")
            self._textbox._textbox.tag_configure("align_right", justify="right")
        except Exception:
            pass
        # 保持置顶
        try:
            self.attributes("-topmost", True)
        except Exception:
            pass

    def set_content(self, text: str, line_alignments: list[str] | None = None) -> None:
        def _do():
            self._set_textbox_readonly(False)
            try:
                self._textbox.delete("1.0", "end")
                if text:
                    self._textbox.insert("1.0", text)
                    tb = self._textbox._textbox
                    try:
                        if line_alignments and len(line_alignments) > 0:
                            lines = text.split("\n")
                            for i, align in enumerate(line_alignments):
                                if i >= len(lines):
                                    break
                                start = f"{i + 1}.0"
                                end = f"{i + 1}.end"
                                tag = "align_left" if align == "left" else "align_right"
                                tb.tag_add(tag, start, end)
                        else:
                            tb.tag_add("all", "1.0", "end")
                    except Exception:
                        try:
                            tb.tag_add("all", "1.0", "end")
                        except Exception:
                            pass
                self._textbox.see("end")
            finally:
                self._set_textbox_readonly(True)

        self.after(0, _do)

    def append_text(self, text: str) -> None:
        def _do():
            self._set_textbox_readonly(False)
            try:
                self._textbox.insert("end", text)
                self._textbox.see("end")
            finally:
                self._set_textbox_readonly(True)

        self.after(0, _do)
