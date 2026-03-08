"""设置页面：API Key、控制台窗口尺寸等"""
import customtkinter as ctk
from typing import Callable

from src.config import (
    CONSOLE_HEIGHT,
    CONSOLE_MIN_HEIGHT,
    CONSOLE_MIN_WIDTH,
    CONSOLE_WIDTH,
    load_settings,
    logger,
    save_settings,
)
from src.theme import (
    ACCENT,
    ACCENT_HOVER,
    BG_CARD,
    BORDER_COLOR,
    BTN_RADIUS,
    CARD_RADIUS,
    INPUT_BG,
    INPUT_RADIUS,
    TEXT_BODY,
    TEXT_HEADING,
)


class SettingsPage(ctk.CTkFrame):
    """设置页面"""

    def __init__(self, master, on_apply_console_size: Callable[[int, int], None] | None = None, **kwargs):
        super().__init__(master, **kwargs)
        self._on_apply_console_size = on_apply_console_size
        self._build_ui()
        self._load_initial()

    def _build_ui(self):
        self.configure(fg_color="transparent")

        # 标题
        title = ctk.CTkLabel(
            self,
            text="设置",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT_HEADING,
        )
        title.pack(pady=(8, 24), padx=0, anchor="w")

        # API Key 卡片
        card = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=CARD_RADIUS,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        card.pack(fill="x", pady=(0, 16))
        api_inner = ctk.CTkFrame(card, fg_color="transparent")
        api_inner.pack(fill="x", padx=24, pady=24)

        ctk.CTkLabel(
            api_inner,
            text="API Key",
            font=ctk.CTkFont(size=14),
            text_color=TEXT_BODY,
        ).pack(anchor="w")
        self.api_key_entry = ctk.CTkEntry(
            api_inner,
            placeholder_text="请输入 DashScope API Key",
            show="*",
            width=420,
            height=40,
            corner_radius=INPUT_RADIUS,
            border_color=BORDER_COLOR,
            fg_color=INPUT_BG,
            text_color=TEXT_BODY,
        )
        self.api_key_entry.pack(anchor="w", pady=(8, 0))

        # 控制台窗口尺寸卡片
        console_card = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=CARD_RADIUS,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        console_card.pack(fill="x", pady=(0, 16))
        console_inner = ctk.CTkFrame(console_card, fg_color="transparent")
        console_inner.pack(fill="x", padx=24, pady=24)
        ctk.CTkLabel(
            console_inner,
            text="控制台窗口",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_HEADING,
        ).pack(anchor="w")
        hint = ctk.CTkLabel(
            console_inner,
            text=f"主窗口宽高（最小 {CONSOLE_MIN_WIDTH}×{CONSOLE_MIN_HEIGHT}，避免内容被裁切）",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_BODY,
        )
        hint.pack(anchor="w", pady=(4, 8))
        row = ctk.CTkFrame(console_inner, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkLabel(row, text="宽度", width=48, text_color=TEXT_BODY).pack(side="left", padx=(0, 8))
        self._console_width = ctk.CTkEntry(
            row,
            width=100,
            height=36,
            corner_radius=INPUT_RADIUS,
            border_color=BORDER_COLOR,
            fg_color=INPUT_BG,
            placeholder_text=str(CONSOLE_WIDTH),
        )
        self._console_width.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(row, text="高度", width=48, text_color=TEXT_BODY).pack(side="left", padx=(0, 8))
        self._console_height = ctk.CTkEntry(
            row,
            width=100,
            height=36,
            corner_radius=INPUT_RADIUS,
            border_color=BORDER_COLOR,
            fg_color=INPUT_BG,
            placeholder_text=str(CONSOLE_HEIGHT),
        )
        self._console_height.pack(side="left")

        # 保存按钮（主按钮）
        self.save_btn = ctk.CTkButton(
            self,
            text="保存",
            command=self._on_save,
            width=120,
            height=40,
            corner_radius=BTN_RADIUS,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="white",
        )
        self.save_btn.pack(pady=24, anchor="w")

    def _load_initial(self):
        settings = load_settings()
        self.api_key_entry.delete(0, "end")
        self.api_key_entry.insert(0, settings.get("api_key", ""))
        w = settings.get("console_width", CONSOLE_WIDTH)
        h = settings.get("console_height", CONSOLE_HEIGHT)
        self._console_width.delete(0, "end")
        self._console_width.insert(0, str(w))
        self._console_height.delete(0, "end")
        self._console_height.insert(0, str(h))

    def _on_save(self):
        api_key = self.api_key_entry.get().strip()
        settings = load_settings()
        settings["api_key"] = api_key
        try:
            cw = CONSOLE_MIN_WIDTH
            ch = CONSOLE_MIN_HEIGHT
            try:
                cw = max(CONSOLE_MIN_WIDTH, int(self._console_width.get().strip() or CONSOLE_WIDTH))
            except (ValueError, TypeError):
                pass
            try:
                ch = max(CONSOLE_MIN_HEIGHT, int(self._console_height.get().strip() or CONSOLE_HEIGHT))
            except (ValueError, TypeError):
                pass
            settings["console_width"] = cw
            settings["console_height"] = ch
            save_settings(settings)
            if self._on_apply_console_size:
                self._on_apply_console_size(cw, ch)
            if logger:
                logger.info("设置已保存")
            self.save_btn.configure(text="已保存")
            self.after(1500, lambda: self.save_btn.configure(text="保存"))
        except Exception as e:
            if logger:
                logger.error("保存失败: %s", e)
