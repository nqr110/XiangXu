"""小窗显示控制台：打开/关闭小窗，窗口/背景/文字配置，恢复默认"""
import customtkinter as ctk

from src.config import OVERLAY_DEFAULTS, load_settings, logger, save_settings
from src.theme import (
    ACCENT,
    BG_CARD,
    BTN_RADIUS,
    BTN_SECONDARY_BORDER,
    BTN_SECONDARY_FG,
    BTN_SECONDARY_HOVER,
    BTN_SECONDARY_TEXT,
    CARD_RADIUS,
    INPUT_RADIUS,
    TEXT_BODY,
    TEXT_HEADING,
)


def _overlay_cfg() -> dict:
    return (load_settings().get("overlay") or {}).copy()


def _save_overlay_cfg(cfg: dict) -> None:
    s = load_settings()
    s["overlay"] = cfg
    save_settings(s)


class OverlayPage(ctk.CTkFrame):
    """小窗显示配置页"""

    def __init__(self, master, on_open_overlay=None, on_close_overlay=None, is_overlay_open=None, on_apply_config=None, **kwargs):
        super().__init__(master, **kwargs)
        self._on_open = on_open_overlay
        self._on_close = on_close_overlay
        self._is_open = is_overlay_open if callable(is_overlay_open) else (lambda: False)
        self._on_apply = on_apply_config
        self._build_ui()

    def _build_ui(self):
        self.configure(fg_color="transparent")

        title = ctk.CTkLabel(
            self,
            text="小窗显示",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT_HEADING,
        )
        title.pack(pady=(8, 24), padx=0, anchor="w")

        # 打开/关闭小窗
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 16))
        self._toggle_btn = ctk.CTkButton(
            btn_frame,
            text="打开小窗",
            command=self._on_toggle,
            width=120,
            height=40,
            corner_radius=BTN_RADIUS,
            fg_color=ACCENT,
            hover_color="#1d4ed8",
            text_color="white",
        )
        self._toggle_btn.pack(side="left")

        # 说明
        hint = ctk.CTkLabel(
            self,
            text="小窗内容与「识别与翻译」页当前会话一致（仅识别 / 仅翻译 / 都），由该页的选项决定。",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_BODY,
        )
        hint.pack(fill="x", pady=(0, 16))

        self._build_section_size()
        self._build_section_bg()
        self._build_section_text()
        self._load_into_entries()

    def _build_section_size(self):
        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=CARD_RADIUS, border_width=1, border_color="#e5e7eb")
        card.pack(fill="x", pady=(0, 12))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=20)
        ctk.CTkLabel(inner, text="窗口大小（屏幕占比 %）", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_HEADING).pack(anchor="w")
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(12, 0))
        ctk.CTkLabel(row, text="宽度", width=48, text_color=TEXT_BODY).pack(side="left", padx=(0, 8))
        self._width_pct = ctk.CTkEntry(row, width=80, height=36, corner_radius=INPUT_RADIUS, placeholder_text="35")
        self._width_pct.pack(side="left", padx=(0, 24))
        ctk.CTkLabel(row, text="高度", width=48, text_color=TEXT_BODY).pack(side="left", padx=(0, 8))
        self._height_pct = ctk.CTkEntry(row, width=80, height=36, corner_radius=INPUT_RADIUS, placeholder_text="40")
        self._height_pct.pack(side="left", padx=(0, 16))
        ctk.CTkButton(
            row,
            text="恢复默认",
            width=90,
            height=32,
            corner_radius=BTN_RADIUS,
            fg_color=BTN_SECONDARY_FG,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=BTN_SECONDARY_TEXT,
            hover_color=BTN_SECONDARY_HOVER,
            command=self._restore_default_size,
        ).pack(side="left")
        self._width_pct.bind("<FocusOut>", lambda e: self._save_and_apply())
        self._height_pct.bind("<FocusOut>", lambda e: self._save_and_apply())

    def _build_section_bg(self):
        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=CARD_RADIUS, border_width=1, border_color="#e5e7eb")
        card.pack(fill="x", pady=(0, 12))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=20)
        ctk.CTkLabel(inner, text="背景", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_HEADING).pack(anchor="w")
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(12, 0))
        ctk.CTkLabel(row, text="颜色", width=48, text_color=TEXT_BODY).pack(side="left", padx=(0, 8))
        self._bg_color = ctk.CTkEntry(row, width=120, height=36, corner_radius=INPUT_RADIUS, placeholder_text="#1a1a1a")
        self._bg_color.pack(side="left", padx=(0, 24))
        ctk.CTkLabel(row, text="透明度", width=56, text_color=TEXT_BODY).pack(side="left", padx=(0, 8))
        self._bg_alpha = ctk.CTkEntry(row, width=80, height=36, corner_radius=INPUT_RADIUS, placeholder_text="0.88")
        self._bg_alpha.pack(side="left", padx=(0, 16))
        ctk.CTkButton(
            row,
            text="恢复默认",
            width=90,
            height=32,
            corner_radius=BTN_RADIUS,
            fg_color=BTN_SECONDARY_FG,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=BTN_SECONDARY_TEXT,
            hover_color=BTN_SECONDARY_HOVER,
            command=self._restore_default_bg,
        ).pack(side="left")
        self._bg_color.bind("<FocusOut>", lambda e: self._save_and_apply())
        self._bg_alpha.bind("<FocusOut>", lambda e: self._save_and_apply())

    def _build_section_text(self):
        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=CARD_RADIUS, border_width=1, border_color="#e5e7eb")
        card.pack(fill="x", pady=(0, 12))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=20)
        ctk.CTkLabel(inner, text="文字", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_HEADING).pack(anchor="w")
        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x", pady=(12, 8))
        ctk.CTkLabel(row1, text="字体", width=48, text_color=TEXT_BODY).pack(side="left", padx=(0, 8))
        self._font_family = ctk.CTkEntry(row1, width=180, height=36, corner_radius=INPUT_RADIUS, placeholder_text="Microsoft YaHei")
        self._font_family.pack(side="left", padx=(0, 24))
        ctk.CTkLabel(row1, text="字号", width=40, text_color=TEXT_BODY).pack(side="left", padx=(0, 8))
        self._font_size = ctk.CTkEntry(row1, width=60, height=36, corner_radius=INPUT_RADIUS, placeholder_text="16")
        self._font_size.pack(side="left", padx=(0, 24))
        ctk.CTkLabel(row1, text="颜色", width=40, text_color=TEXT_BODY).pack(side="left", padx=(0, 8))
        self._text_color = ctk.CTkEntry(row1, width=100, height=36, corner_radius=INPUT_RADIUS, placeholder_text="#e5e5e5")
        self._text_color.pack(side="left", padx=(0, 16))
        ctk.CTkButton(
            row1,
            text="恢复默认",
            width=90,
            height=32,
            corner_radius=BTN_RADIUS,
            fg_color=BTN_SECONDARY_FG,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=BTN_SECONDARY_TEXT,
            hover_color=BTN_SECONDARY_HOVER,
            command=self._restore_default_text,
        ).pack(side="left")

        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 0))
        ctk.CTkLabel(row2, text="行距", width=48, text_color=TEXT_BODY).pack(side="left", padx=(0, 8))
        self._line_spacing = ctk.CTkEntry(row2, width=80, height=36, corner_radius=INPUT_RADIUS, placeholder_text="8")
        self._line_spacing.pack(side="left", padx=(0, 24))
        ctk.CTkLabel(row2, text="对齐", width=40, text_color=TEXT_BODY).pack(side="left", padx=(0, 8))
        self._align = ctk.CTkOptionMenu(
            row2,
            values=["left", "center", "right"],
            width=120,
            height=36,
            command=lambda v: self._save_and_apply(),
        )
        self._align.pack(side="left")
        self._font_family.bind("<FocusOut>", lambda e: self._save_and_apply())
        self._font_size.bind("<FocusOut>", lambda e: self._save_and_apply())
        self._text_color.bind("<FocusOut>", lambda e: self._save_and_apply())
        self._line_spacing.bind("<FocusOut>", lambda e: self._save_and_apply())

    def _load_into_entries(self):
        cfg = _overlay_cfg()
        def set_entry(e, key, default):
            v = cfg.get(key, default)
            e.delete(0, "end")
            if v is not None and str(v).strip():
                e.insert(0, str(v))
        def set_align(v):
            self._align.set(v if v in ("left", "center", "right") else "left")
        d = OVERLAY_DEFAULTS["overlay"]
        set_entry(self._width_pct, "width_pct", d["width_pct"])
        set_entry(self._height_pct, "height_pct", d["height_pct"])
        set_entry(self._bg_color, "bg_color", d["bg_color"])
        set_entry(self._bg_alpha, "bg_alpha", d["bg_alpha"])
        set_entry(self._font_family, "font_family", d["font_family"])
        set_entry(self._font_size, "font_size", d["font_size"])
        set_entry(self._text_color, "text_color", d["text_color"])
        set_entry(self._line_spacing, "line_spacing", d["line_spacing"])
        set_align(cfg.get("align", d["align"]))

    def _collect_overlay_cfg(self) -> dict:
        cfg = _overlay_cfg()
        d = OVERLAY_DEFAULTS["overlay"]
        def get_num(e, key, default):
            try:
                return int(float(e.get().strip() or default))
            except Exception:
                return default
        def get_float(e, key, default):
            try:
                return float(e.get().strip() or default)
            except Exception:
                return default
        cfg["width_pct"] = get_float(self._width_pct, "width_pct", d["width_pct"])
        cfg["height_pct"] = get_float(self._height_pct, "height_pct", d["height_pct"])
        cfg["bg_color"] = (self._bg_color.get() or d["bg_color"]).strip()
        cfg["bg_alpha"] = get_float(self._bg_alpha, "bg_alpha", d["bg_alpha"])
        cfg["font_family"] = (self._font_family.get() or d["font_family"]).strip()
        cfg["font_size"] = get_num(self._font_size, "font_size", d["font_size"])
        cfg["text_color"] = (self._text_color.get() or d["text_color"]).strip()
        cfg["line_spacing"] = get_num(self._line_spacing, "line_spacing", d["line_spacing"])
        cfg["align"] = (self._align.get() or d["align"]).strip().lower() or "left"
        if cfg["align"] not in ("left", "center", "right"):
            cfg["align"] = "left"
        return cfg

    def _save_and_apply(self):
        cfg = self._collect_overlay_cfg()
        _save_overlay_cfg(cfg)
        if self._on_apply:
            self._on_apply()
        if logger:
            logger.debug("小窗配置已保存并应用")

    def _restore_default_size(self):
        d = OVERLAY_DEFAULTS["overlay"]
        self._width_pct.delete(0, "end")
        self._width_pct.insert(0, str(d["width_pct"]))
        self._height_pct.delete(0, "end")
        self._height_pct.insert(0, str(d["height_pct"]))
        self._save_and_apply()

    def _restore_default_bg(self):
        d = OVERLAY_DEFAULTS["overlay"]
        self._bg_color.delete(0, "end")
        self._bg_color.insert(0, str(d["bg_color"]))
        self._bg_alpha.delete(0, "end")
        self._bg_alpha.insert(0, str(d["bg_alpha"]))
        self._save_and_apply()

    def _restore_default_text(self):
        d = OVERLAY_DEFAULTS["overlay"]
        self._font_family.delete(0, "end")
        self._font_family.insert(0, str(d["font_family"]))
        self._font_size.delete(0, "end")
        self._font_size.insert(0, str(d["font_size"]))
        self._text_color.delete(0, "end")
        self._text_color.insert(0, str(d["text_color"]))
        self._line_spacing.delete(0, "end")
        self._line_spacing.insert(0, str(d["line_spacing"]))
        self._align.set(d["align"])
        self._save_and_apply()

    def _on_toggle(self):
        if self._is_open():
            if self._on_close:
                self._on_close()
            self._toggle_btn.configure(text="打开小窗")
        else:
            if self._on_open:
                self._on_open()
            self._toggle_btn.configure(text="关闭小窗")

    def set_overlay_open(self, open: bool):
        """由 App 在打开/关闭小窗后调用，更新按钮文案"""
        self._toggle_btn.configure(text="关闭小窗" if open else "打开小窗")

    def refresh_toggle_button(self):
        """进入页面时根据当前小窗状态刷新按钮"""
        self._toggle_btn.configure(text="关闭小窗" if self._is_open() else "打开小窗")
        self._load_into_entries()
