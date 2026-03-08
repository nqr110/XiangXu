"""小窗显示控制台：打开/关闭小窗，窗口/背景/文字配置，恢复默认"""
import customtkinter as ctk

from src.config import OVERLAY_DEFAULTS, load_settings, logger, save_settings
from src.theme import (
    ACCENT,
    ACCENT_HOVER,
    BG_CARD,
    BORDER_COLOR,
    BTN_RADIUS,
    BTN_SECONDARY_BORDER,
    BTN_SECONDARY_FG,
    BTN_SECONDARY_HOVER,
    BTN_SECONDARY_TEXT,
    CARD_RADIUS,
    INPUT_BORDER_WIDTH,
    INPUT_RADIUS,
    OPTION_MENU_BUTTON,
    OPTION_MENU_INNER_RADIUS,
    OPTION_MENU_BUTTON_HOVER,
    OPTION_MENU_DROPDOWN_FG,
    OPTION_MENU_DROPDOWN_HOVER,
    OPTION_MENU_FG,
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

    def __init__(self, master, on_open_overlay=None, on_close_overlay=None, is_overlay_open=None, on_apply_config=None, on_lock_overlay=None, **kwargs):
        super().__init__(master, **kwargs)
        self._on_open = on_open_overlay
        self._on_close = on_close_overlay
        self._is_open = is_overlay_open if callable(is_overlay_open) else (lambda: False)
        self._on_apply = on_apply_config
        self._on_lock = on_lock_overlay if callable(on_lock_overlay) else None
        self._overlay_locked = False
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
            hover_color=ACCENT_HOVER,
            text_color="white",
        )
        self._toggle_btn.pack(side="left", padx=(0, 12))
        self._simple_btn = ctk.CTkButton(
            btn_frame,
            text="简洁模式",
            command=self._toggle_simple_mode,
            width=100,
            height=40,
            corner_radius=BTN_RADIUS,
            fg_color=BTN_SECONDARY_FG,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=TEXT_BODY,
            hover_color=BTN_SECONDARY_HOVER,
        )
        self._simple_btn.pack(side="left", padx=(0, 12))
        self._split_btn = ctk.CTkButton(
            btn_frame,
            text="拆分字幕",
            command=self._toggle_split_mode,
            width=100,
            height=40,
            corner_radius=BTN_RADIUS,
            fg_color=BTN_SECONDARY_FG,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=TEXT_BODY,
            hover_color=BTN_SECONDARY_HOVER,
        )
        self._split_btn.pack(side="left", padx=(0, 12))
        self._lock_btn = ctk.CTkButton(
            btn_frame,
            text="窗口锁定",
            command=self._on_lock_click,
            width=100,
            height=40,
            corner_radius=BTN_RADIUS,
            fg_color=BTN_SECONDARY_FG,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=TEXT_BODY,
            hover_color=BTN_SECONDARY_HOVER,
        )
        self._lock_btn.pack(side="left")
        self._lock_btn.configure(state="disabled")

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
        self._refresh_mode_buttons()

    def _build_section_size(self):
        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=CARD_RADIUS, border_width=1, border_color=BORDER_COLOR)
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
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            row,
            text="恢复默认位置",
            width=100,
            height=32,
            corner_radius=BTN_RADIUS,
            fg_color=BTN_SECONDARY_FG,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=BTN_SECONDARY_TEXT,
            hover_color=BTN_SECONDARY_HOVER,
            command=self._restore_default_position,
        ).pack(side="left")
        self._width_pct.bind("<FocusOut>", lambda e: self._save_and_apply())
        self._height_pct.bind("<FocusOut>", lambda e: self._save_and_apply())

        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x", pady=(12, 0))
        ctk.CTkLabel(row2, text="边角", width=48, text_color=TEXT_BODY).pack(side="left", padx=(0, 8))
        corner_style_wrap = ctk.CTkFrame(
            row2,
            fg_color=OPTION_MENU_FG,
            corner_radius=INPUT_RADIUS,
            border_width=INPUT_BORDER_WIDTH,
            border_color=BORDER_COLOR,
        )
        corner_style_wrap.pack(side="left", padx=(0, 16))
        self._corner_style = ctk.CTkOptionMenu(
            corner_style_wrap,
            values=["圆角", "直角"],
            width=100,
            height=36,
            corner_radius=OPTION_MENU_INNER_RADIUS,
            fg_color=OPTION_MENU_FG,
            button_color=OPTION_MENU_BUTTON,
            button_hover_color=OPTION_MENU_BUTTON_HOVER,
            dropdown_fg_color=OPTION_MENU_DROPDOWN_FG,
            dropdown_hover_color=OPTION_MENU_DROPDOWN_HOVER,
            text_color=TEXT_BODY,
            command=lambda v: self._save_and_apply(),
        )
        self._corner_style.pack(padx=INPUT_BORDER_WIDTH, pady=INPUT_BORDER_WIDTH)
        ctk.CTkLabel(row2, text="圆角弧度", width=64, text_color=TEXT_BODY).pack(side="left", padx=(0, 8))
        self._corner_radius_entry = ctk.CTkEntry(
            row2, width=64, height=36, corner_radius=INPUT_RADIUS, placeholder_text="12",
        )
        self._corner_radius_entry.pack(side="left")
        self._corner_radius_entry.bind("<FocusOut>", lambda e: self._save_and_apply())

    def _build_section_bg(self):
        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=CARD_RADIUS, border_width=1, border_color=BORDER_COLOR)
        card.pack(fill="x", pady=(0, 12))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=20)
        ctk.CTkLabel(inner, text="背景", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_HEADING).pack(anchor="w")
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(12, 0))
        ctk.CTkLabel(row, text="颜色", width=48, text_color=TEXT_BODY).pack(side="left", padx=(0, 8))
        self._bg_color = ctk.CTkEntry(row, width=120, height=36, corner_radius=INPUT_RADIUS, placeholder_text="#1a1a1a")
        self._bg_color.pack(side="left", padx=(0, 24))
        ctk.CTkLabel(row, text="背景透明度", width=72, text_color=TEXT_BODY).pack(side="left", padx=(0, 8))
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
        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=CARD_RADIUS, border_width=1, border_color=BORDER_COLOR)
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
        self._text_color.pack(side="left", padx=(0, 12))
        ctk.CTkLabel(row1, text="透明度", width=48, text_color=TEXT_BODY).pack(side="left", padx=(0, 8))
        self._text_alpha = ctk.CTkEntry(row1, width=60, height=36, corner_radius=INPUT_RADIUS, placeholder_text="1")
        self._text_alpha.pack(side="left", padx=(0, 16))
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
        align_wrap = ctk.CTkFrame(
            row2,
            fg_color=OPTION_MENU_FG,
            corner_radius=INPUT_RADIUS,
            border_width=INPUT_BORDER_WIDTH,
            border_color=BORDER_COLOR,
        )
        align_wrap.pack(side="left")
        self._align = ctk.CTkOptionMenu(
            align_wrap,
            values=["left", "center", "right"],
            width=120,
            height=36,
            corner_radius=OPTION_MENU_INNER_RADIUS,
            fg_color=OPTION_MENU_FG,
            button_color=OPTION_MENU_BUTTON,
            button_hover_color=OPTION_MENU_BUTTON_HOVER,
            dropdown_fg_color=OPTION_MENU_DROPDOWN_FG,
            dropdown_hover_color=OPTION_MENU_DROPDOWN_HOVER,
            text_color=TEXT_BODY,
            command=lambda v: self._save_and_apply(),
        )
        self._align.pack(padx=INPUT_BORDER_WIDTH, pady=INPUT_BORDER_WIDTH)
        self._font_family.bind("<FocusOut>", lambda e: self._save_and_apply())
        self._font_size.bind("<FocusOut>", lambda e: self._save_and_apply())
        self._text_color.bind("<FocusOut>", lambda e: self._save_and_apply())
        self._text_alpha.bind("<FocusOut>", lambda e: self._save_and_apply())
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
        def set_corner(v):
            self._corner_style.set("圆角" if v == "rounded" else "直角")
        d = OVERLAY_DEFAULTS["overlay"]
        set_entry(self._width_pct, "width_pct", d["width_pct"])
        set_entry(self._height_pct, "height_pct", d["height_pct"])
        set_corner(cfg.get("corner_style", d["corner_style"]))
        set_entry(self._corner_radius_entry, "corner_radius", d.get("corner_radius", 12))
        set_entry(self._bg_color, "bg_color", d["bg_color"])
        set_entry(self._bg_alpha, "bg_alpha", d["bg_alpha"])
        set_entry(self._font_family, "font_family", d["font_family"])
        set_entry(self._font_size, "font_size", d["font_size"])
        set_entry(self._text_color, "text_color", d["text_color"])
        set_entry(self._text_alpha, "text_alpha", d["text_alpha"])
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
        corner_val = (self._corner_style.get() or "圆角").strip()
        cfg["corner_style"] = "rounded" if corner_val == "圆角" else "square"
        cfg["corner_radius"] = max(0, min(80, get_num(self._corner_radius_entry, "corner_radius", d.get("corner_radius", 12))))
        cfg["bg_color"] = (self._bg_color.get() or d["bg_color"]).strip()
        cfg["bg_alpha"] = get_float(self._bg_alpha, "bg_alpha", d["bg_alpha"])
        cfg["font_family"] = (self._font_family.get() or d["font_family"]).strip()
        cfg["font_size"] = get_num(self._font_size, "font_size", d["font_size"])
        cfg["text_color"] = (self._text_color.get() or d["text_color"]).strip()
        cfg["text_alpha"] = get_float(self._text_alpha, "text_alpha", d["text_alpha"])
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
        self._corner_style.set("圆角" if d.get("corner_style", "rounded") == "rounded" else "直角")
        self._corner_radius_entry.delete(0, "end")
        self._corner_radius_entry.insert(0, str(d.get("corner_radius", 12)))
        self._save_and_apply()

    def _restore_default_position(self):
        """清除已保存的小窗位置，使小窗使用默认居中位置"""
        cfg = _overlay_cfg()
        cfg.pop("position_x_pct", None)
        cfg.pop("position_y_pct", None)
        cfg.pop("position_x", None)
        cfg.pop("position_y", None)
        _save_overlay_cfg(cfg)
        if self._on_apply:
            self._on_apply()
        if logger:
            logger.debug("小窗位置已恢复默认")

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
        self._text_alpha.delete(0, "end")
        self._text_alpha.insert(0, str(d["text_alpha"]))
        self._line_spacing.delete(0, "end")
        self._line_spacing.insert(0, str(d["line_spacing"]))
        self._align.set(d["align"])
        self._save_and_apply()

    def _toggle_simple_mode(self):
        cfg = _overlay_cfg()
        cfg["simple_mode"] = not cfg.get("simple_mode", False)
        _save_overlay_cfg(cfg)
        self._refresh_mode_buttons()
        if self._on_apply:
            self._on_apply()

    def _toggle_split_mode(self):
        cfg = _overlay_cfg()
        cfg["split_subtitle_mode"] = not cfg.get("split_subtitle_mode", False)
        _save_overlay_cfg(cfg)
        self._refresh_mode_buttons()
        if self._on_apply:
            self._on_apply()

    def _refresh_mode_buttons(self):
        cfg = _overlay_cfg()
        simple = cfg.get("simple_mode", False)
        split = cfg.get("split_subtitle_mode", False)
        self._simple_btn.configure(
            text="简洁模式 ✓" if simple else "简洁模式",
            fg_color=ACCENT if simple else BTN_SECONDARY_FG,
            text_color="white" if simple else BTN_SECONDARY_TEXT,
        )
        self._split_btn.configure(
            text="拆分字幕 ✓" if split else "拆分字幕",
            fg_color=ACCENT if split else BTN_SECONDARY_FG,
            text_color="white" if split else BTN_SECONDARY_TEXT,
        )
        self._lock_btn.configure(
            text="窗口锁定 ✓" if self._overlay_locked else "窗口锁定",
            fg_color=ACCENT if self._overlay_locked else BTN_SECONDARY_FG,
            text_color="white" if self._overlay_locked else BTN_SECONDARY_TEXT,
        )

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
        """由 App 在打开/关闭小窗后调用，更新按钮文案与锁定按钮状态"""
        self._toggle_btn.configure(text="关闭小窗" if open else "打开小窗")
        if open:
            self._lock_btn.configure(state="normal")
        else:
            self._lock_btn.configure(state="disabled")
            self._overlay_locked = False
        self._update_lock_btn_text()

    def set_overlay_locked(self, locked: bool) -> None:
        """由 App 在打开小窗后调用，重置为未锁定并更新锁定按钮文案。"""
        self._overlay_locked = locked
        self._update_lock_btn_text()

    def _update_lock_btn_text(self) -> None:
        """更新锁定按钮文案与样式，与「简洁模式」「拆分字幕」一致：打勾时高亮。"""
        locked = self._overlay_locked
        self._lock_btn.configure(
            text="窗口锁定 ✓" if locked else "窗口锁定",
            fg_color=ACCENT if locked else BTN_SECONDARY_FG,
            text_color="white" if locked else BTN_SECONDARY_TEXT,
        )

    def _on_lock_click(self) -> None:
        self._overlay_locked = not self._overlay_locked
        if self._on_lock:
            self._on_lock(self._overlay_locked)
        self._update_lock_btn_text()

    def refresh_toggle_button(self):
        """进入页面时根据当前小窗状态刷新按钮（不重载配置表单，避免 I/O 与大量控件更新）"""
        self._toggle_btn.configure(text="关闭小窗" if self._is_open() else "打开小窗")
        open_ = self._is_open()
        self._lock_btn.configure(state="normal" if open_ else "disabled")
        if not open_:
            self._overlay_locked = False
        self._update_lock_btn_text()
        self._refresh_mode_buttons()
