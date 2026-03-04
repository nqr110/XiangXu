"""设置页面：API Key 输入与持久化"""
import customtkinter as ctk

from src.config import load_settings, logger, save_settings
from src.theme import (
    ACCENT,
    BG_CARD,
    BTN_RADIUS,
    CARD_RADIUS,
    INPUT_RADIUS,
    TEXT_BODY,
    TEXT_HEADING,
)


class SettingsPage(ctk.CTkFrame):
    """设置页面"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
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
            border_color="#e5e7eb",
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
            border_color="#e5e7eb",
            fg_color="#fafafa",
            text_color=TEXT_BODY,
        )
        self.api_key_entry.pack(anchor="w", pady=(8, 0))

        # 保存按钮（主按钮）
        self.save_btn = ctk.CTkButton(
            self,
            text="保存",
            command=self._on_save,
            width=120,
            height=40,
            corner_radius=BTN_RADIUS,
            fg_color=ACCENT,
            hover_color="#1d4ed8",
            text_color="white",
        )
        self.save_btn.pack(pady=24, anchor="w")

    def _load_initial(self):
        settings = load_settings()
        self.api_key_entry.delete(0, "end")
        self.api_key_entry.insert(0, settings.get("api_key", ""))

    def _on_save(self):
        api_key = self.api_key_entry.get().strip()
        settings = load_settings()
        settings["api_key"] = api_key
        try:
            save_settings(settings)
            if logger:
                logger.info("设置已保存")
            self.save_btn.configure(text="已保存")
            self.after(1500, lambda: self.save_btn.configure(text="保存"))
        except Exception as e:
            if logger:
                logger.error("保存失败: %s", e)
