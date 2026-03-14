"""过滤器页面：音质处理（降噪、人声增强）"""
import customtkinter as ctk

from src.config import load_settings, logger, save_settings
from src.theme import (
    ACCENT,
    ACCENT_HOVER,
    BG_CARD,
    BORDER_COLOR,
    BTN_RADIUS,
    CARD_RADIUS,
    TEXT_BODY,
    TEXT_HEADING,
)


class FilterPage(ctk.CTkFrame):
    """过滤器页面：音质处理（降噪、人声增强）"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._build_ui()
        self._load_initial()

    def _build_ui(self):
        self.configure(fg_color="transparent")

        title = ctk.CTkLabel(
            self,
            text="过滤器",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT_HEADING,
        )
        title.pack(pady=(8, 8), padx=0, anchor="w")

        hint = ctk.CTkLabel(
            self,
            text="可选开启降噪与人声增强，以改善识别效果。",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_BODY,
        )
        hint.pack(anchor="w", pady=(0, 16))

        # 传译进行中锁定提示（默认隐藏）
        self._lock_hint = ctk.CTkLabel(
            self,
            text="传译进行中，请停止后修改",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_BODY,
        )
        self._lock_hint.pack(anchor="w", pady=(0, 8))
        self._lock_hint.pack_forget()

        # 音质处理卡片（降噪、人声增强）
        try:
            from src.services.audio_processing import _get_denoiser
            self._denoiser_available = _get_denoiser() is not None
        except Exception:
            self._denoiser_available = False
        self._audio_processing_card = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=CARD_RADIUS,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        self._audio_processing_card.pack(fill="x", pady=(0, 16))
        ap_inner = ctk.CTkFrame(self._audio_processing_card, fg_color="transparent")
        ap_inner.pack(fill="x", padx=24, pady=24)
        ctk.CTkLabel(
            ap_inner,
            text="音质处理",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_HEADING,
        ).pack(anchor="w")
        self._denoise_var = ctk.BooleanVar(value=False)
        self._denoise_switch = ctk.CTkSwitch(
            ap_inner,
            text="降噪" if self._denoiser_available else "降噪（未安装 pyrnnoise，不可用）",
            variable=self._denoise_var,
            font=ctk.CTkFont(size=13),
            text_color=TEXT_BODY,
        )
        self._denoise_switch.pack(anchor="w", pady=4)
        if not self._denoiser_available:
            self._denoise_switch.configure(state="disabled")
        self._voice_enhance_var = ctk.BooleanVar(value=False)
        self._voice_enhance_switch = ctk.CTkSwitch(
            ap_inner,
            text="人声增强",
            variable=self._voice_enhance_var,
            font=ctk.CTkFont(size=13),
            text_color=TEXT_BODY,
        )
        self._voice_enhance_switch.pack(anchor="w", pady=4)

        # 保存按钮
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 8))
        self._save_btn = ctk.CTkButton(
            btn_row,
            text="保存",
            command=self._on_save,
            width=120,
            height=40,
            corner_radius=BTN_RADIUS,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="white",
        )
        self._save_btn.pack(side="left", padx=(0, 12))

    def _load_initial(self):
        settings = load_settings()
        self._denoise_var.set(settings.get("audio_denoise_enabled", False))
        self._voice_enhance_var.set(settings.get("audio_voice_enhance_enabled", False))

    def _on_save(self):
        settings = load_settings()
        settings["audio_denoise_enabled"] = self._denoise_var.get()
        settings["audio_voice_enhance_enabled"] = self._voice_enhance_var.get()
        try:
            save_settings(settings)
            if logger:
                logger.info("过滤器配置已保存")
            self._save_btn.configure(text="已保存")
            self.after(1500, lambda: self._save_btn.configure(text="保存"))
        except Exception as e:
            if logger:
                logger.error("保存过滤器配置失败: %s", e)

    def set_options_locked(self, locked: bool) -> None:
        """传译进行中锁定所有可配置项，避免误以为可实时生效。"""
        if locked:
            self._lock_hint.pack(anchor="w", pady=(0, 8))
        else:
            self._lock_hint.pack_forget()
        state = "disabled" if locked else "normal"
        self._save_btn.configure(state=state)
        self._voice_enhance_switch.configure(state=state)
        if locked:
            self._denoise_switch.configure(state="disabled")
        else:
            self._denoise_switch.configure(state="normal" if self._denoiser_available else "disabled")
