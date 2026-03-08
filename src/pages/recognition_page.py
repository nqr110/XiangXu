"""识别与翻译页面：控制区、显示区、一键清空、DisplayTarget 预留"""
import customtkinter as ctk

from src.config import (
    SOURCE_LANGUAGE_OPTIONS,
    TARGET_LANGUAGE_OPTIONS,
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
    BTN_SECONDARY_BORDER,
    BTN_SECONDARY_FG,
    BTN_SECONDARY_HOVER,
    BTN_SECONDARY_TEXT,
    CARD_RADIUS,
    INPUT_BORDER_WIDTH,
    INPUT_BG,
    INPUT_RADIUS,
    OPTION_MENU_BUTTON,
    OPTION_MENU_INNER_RADIUS,
    OPTION_MENU_BUTTON_HOVER,
    OPTION_MENU_DROPDOWN_FG,
    OPTION_MENU_DROPDOWN_HOVER,
    OPTION_MENU_FG,
    TEXT_BODY,
)


class DisplayTarget:
    """显示目标接口，预留后期切换为透明悬浮窗"""

    def append_text(self, text: str) -> None:
        """追加文本"""
        raise NotImplementedError

    def update_or_append(self, text: str, kind: str, sentence_end: bool) -> None:
        """流式更新或追加（已废弃，使用 update_batch）"""
        raise NotImplementedError

    def update_batch(self, recog_text: str, trans_text: str, recog_end: bool, trans_end: bool) -> None:
        """批量更新：同一事件内同时更新识别与翻译，仅固化一次"""
        raise NotImplementedError

    def clear(self) -> None:
        """清空内容"""
        raise NotImplementedError


class TextboxDisplayTarget(DisplayTarget):
    """默认实现：写入 CTkTextbox，支持流式覆盖显示（字符串缓冲模型）"""

    def __init__(self, textbox: ctk.CTkTextbox):
        self._textbox = textbox
        self._finalized_content = ""  # 已结束的句子
        self._streaming_recognition = ""
        self._streaming_translation = ""

    def append_text(self, text: str) -> None:
        self._textbox.insert("end", text)
        self._textbox.see("end")

    def _build_streaming_block(self) -> str:
        lines = []
        if self._streaming_recognition:
            lines.append(f"识别: {self._streaming_recognition}")
        if self._streaming_translation:
            lines.append(f"翻译: {self._streaming_translation}")
        return "\n".join(lines) + ("\n" if lines else "")

    def update_or_append(self, text: str, kind: str, sentence_end: bool) -> None:
        if kind == "recognition":
            self.update_batch(text, self._streaming_translation, sentence_end, False)
        else:
            self.update_batch(self._streaming_recognition, text, False, sentence_end)

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
        self._textbox.delete("1.0", "end")
        self._textbox.insert("1.0", full)
        self._textbox.see("end")

    def clear(self) -> None:
        self._textbox.delete("1.0", "end")
        self._finalized_content = ""
        self._streaming_recognition = ""
        self._streaming_translation = ""


# 预留：透明置顶悬浮窗实现（后期可替换 TextboxDisplayTarget）
# class OverlayDisplay(DisplayTarget):
#     """透明置顶悬浮窗，使用 CTkToplevel + attributes('-topmost', True) + 透明色"""
#     def __init__(self, root):
#         self._win = ctk.CTkToplevel(root)
#         self._win.attributes("-topmost", True)
#         # self._win.attributes("-transparentcolor", "white")  # 需配合 -alpha
#     def append_text(self, text: str) -> None: ...
#     def clear(self) -> None: ...


class RecognitionPage(ctk.CTkFrame):
    """识别与翻译页面"""

    def __init__(self, master, on_start=None, on_stop=None, **kwargs):
        super().__init__(master, **kwargs)
        self._on_start = on_start
        self._on_stop = on_stop
        self._display: DisplayTarget | None = None
        self._build_ui()

    def _build_ui(self):
        self.configure(fg_color="transparent")

        # 控制区（卡片）
        ctrl_card = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=CARD_RADIUS,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        ctrl_card.pack(fill="x", pady=(0, 16))
        ctrl_frame = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=20, pady=16)

        self.recog_var = ctk.BooleanVar(value=True)
        self.trans_var = ctk.BooleanVar(value=True)
        self.recog_btn = ctk.CTkButton(
            ctrl_frame,
            text="识别",
            command=self._toggle_recog,
            width=72,
            height=36,
            corner_radius=BTN_RADIUS,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="white",
            border_width=0,
        )
        self.recog_btn.pack(side="left", padx=(0, 12))
        self.trans_btn = ctk.CTkButton(
            ctrl_frame,
            text="翻译",
            command=self._toggle_trans,
            width=72,
            height=36,
            corner_radius=BTN_RADIUS,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="white",
            border_width=0,
        )
        self.trans_btn.pack(side="left", padx=(0, 24))
        self._update_toggle_buttons()

        self.start_btn = ctk.CTkButton(
            ctrl_frame,
            text="开始",
            command=self._on_start_click,
            width=88,
            height=36,
            corner_radius=BTN_RADIUS,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="white",
        )
        self.start_btn.pack(side="left", padx=(0, 10))
        self.stop_btn = ctk.CTkButton(
            ctrl_frame,
            text="停止",
            command=self._on_stop_click,
            width=88,
            height=36,
            state="disabled",
            corner_radius=BTN_RADIUS,
            fg_color=BTN_SECONDARY_FG,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=BTN_SECONDARY_TEXT,
            hover_color=BTN_SECONDARY_HOVER,
        )
        self.stop_btn.pack(side="left", padx=(0, 10))
        clear_btn = ctk.CTkButton(
            ctrl_frame,
            text="一键清空",
            command=self._on_clear,
            width=88,
            height=36,
            corner_radius=BTN_RADIUS,
            fg_color=BTN_SECONDARY_FG,
            border_width=1,
            border_color=BTN_SECONDARY_BORDER,
            text_color=BTN_SECONDARY_TEXT,
            hover_color=BTN_SECONDARY_HOVER,
        )
        clear_btn.pack(side="left")

        # 识别与翻译语言（单独一个卡片，在控制区下方）
        lang_card = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=CARD_RADIUS,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        lang_card.pack(fill="x", pady=(0, 16))
        lang_frame = ctk.CTkFrame(lang_card, fg_color="transparent")
        lang_frame.pack(fill="x", padx=20, pady=16)
        ctk.CTkLabel(lang_frame, text="源语言", width=56, text_color=TEXT_BODY).pack(side="left", padx=(0, 8))
        self._source_lang_var = ctk.StringVar(value="英文")
        source_option_wrap = ctk.CTkFrame(
            lang_frame,
            fg_color=OPTION_MENU_FG,
            corner_radius=INPUT_RADIUS,
            border_width=INPUT_BORDER_WIDTH,
            border_color=BORDER_COLOR,
        )
        source_option_wrap.pack(side="left", padx=(0, 16))
        self._source_option = ctk.CTkOptionMenu(
            source_option_wrap,
            values=[n for _, n in SOURCE_LANGUAGE_OPTIONS],
            variable=self._source_lang_var,
            width=120,
            height=32,
            corner_radius=OPTION_MENU_INNER_RADIUS,
            fg_color=OPTION_MENU_FG,
            button_color=OPTION_MENU_BUTTON,
            button_hover_color=OPTION_MENU_BUTTON_HOVER,
            dropdown_fg_color=OPTION_MENU_DROPDOWN_FG,
            dropdown_hover_color=OPTION_MENU_DROPDOWN_HOVER,
            text_color=TEXT_BODY,
            command=self._on_language_changed,
        )
        self._source_option.pack(padx=INPUT_BORDER_WIDTH, pady=INPUT_BORDER_WIDTH)
        ctk.CTkLabel(lang_frame, text="翻译目标", width=56, text_color=TEXT_BODY).pack(side="left", padx=(0, 8))
        self._target_lang_var = ctk.StringVar(value="中文")
        target_option_wrap = ctk.CTkFrame(
            lang_frame,
            fg_color=OPTION_MENU_FG,
            corner_radius=INPUT_RADIUS,
            border_width=INPUT_BORDER_WIDTH,
            border_color=BORDER_COLOR,
        )
        target_option_wrap.pack(side="left")
        self._target_option = ctk.CTkOptionMenu(
            target_option_wrap,
            values=[n for _, n in TARGET_LANGUAGE_OPTIONS],
            variable=self._target_lang_var,
            width=120,
            height=32,
            corner_radius=OPTION_MENU_INNER_RADIUS,
            fg_color=OPTION_MENU_FG,
            button_color=OPTION_MENU_BUTTON,
            button_hover_color=OPTION_MENU_BUTTON_HOVER,
            dropdown_fg_color=OPTION_MENU_DROPDOWN_FG,
            dropdown_hover_color=OPTION_MENU_DROPDOWN_HOVER,
            text_color=TEXT_BODY,
            command=self._on_language_changed,
        )
        self._target_option.pack(padx=INPUT_BORDER_WIDTH, pady=INPUT_BORDER_WIDTH)

        self._load_language_initial()

        # 显示区（卡片）
        display_card = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=CARD_RADIUS,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        display_card.pack(fill="both", expand=True)
        inner = ctk.CTkFrame(display_card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=16)
        self.textbox = ctk.CTkTextbox(
            inner,
            wrap="word",
            font=ctk.CTkFont(size=14),
            fg_color=INPUT_BG,
            border_width=1,
            border_color=BORDER_COLOR,
            corner_radius=INPUT_RADIUS,
            text_color=TEXT_BODY,
        )
        self.textbox.pack(fill="both", expand=True)
        self._display = TextboxDisplayTarget(self.textbox)

    def _update_toggle_buttons(self):
        """根据 recog_var / trans_var 刷新「识别」「翻译」切换按钮样式"""
        for btn, var in [(self.recog_btn, self.recog_var), (self.trans_btn, self.trans_var)]:
            if var.get():
                btn.configure(
                    fg_color=ACCENT,
                    hover_color=ACCENT_HOVER,
                    text_color="white",
                    border_width=0,
                )
            else:
                btn.configure(
                    fg_color=BTN_SECONDARY_FG,
                    hover_color=BTN_SECONDARY_HOVER,
                    text_color=BTN_SECONDARY_TEXT,
                    border_width=1,
                    border_color=BTN_SECONDARY_BORDER,
                )

    def _toggle_recog(self):
        self.recog_var.set(not self.recog_var.get())
        self._update_toggle_buttons()

    def _toggle_trans(self):
        self.trans_var.set(not self.trans_var.get())
        self._update_toggle_buttons()

    def _on_start_click(self):
        if self._on_start:
            self._on_start(
                transcription_enabled=self.recog_var.get(),
                translation_enabled=self.trans_var.get(),
            )

    def _on_stop_click(self):
        if self._on_stop:
            self._on_stop()
        self.set_running(False)

    def _on_clear(self):
        if self._display:
            self._display.clear()

    def _load_language_initial(self):
        """从 config 回填源语言与目标语言"""
        settings = load_settings()
        src_val = settings.get("source_language", "en")
        src_to_name = {v: n for v, n in SOURCE_LANGUAGE_OPTIONS}
        self._source_lang_var.set(src_to_name.get(src_val, "英文"))
        tgt_list = settings.get("translation_target_languages", ["zh"])
        tgt_val = tgt_list[0] if tgt_list else "zh"
        tgt_to_name = {v: n for v, n in TARGET_LANGUAGE_OPTIONS}
        self._target_lang_var.set(tgt_to_name.get(tgt_val, "中文"))

    def _on_language_changed(self, _value=None):
        """下拉变更时写入 config 并持久化"""
        try:
            settings = load_settings()
            name_to_src = {n: v for v, n in SOURCE_LANGUAGE_OPTIONS}
            name_to_tgt = {n: v for v, n in TARGET_LANGUAGE_OPTIONS}
            settings["source_language"] = name_to_src.get(self._source_lang_var.get(), "en")
            settings["translation_target_languages"] = [name_to_tgt.get(self._target_lang_var.get(), "zh")]
            save_settings(settings)
            if logger:
                logger.debug("识别与翻译语言已保存")
        except Exception as e:
            if logger:
                logger.error("保存语言设置失败: %s", e)

    def get_display_target(self) -> DisplayTarget | None:
        return self._display

    def set_callbacks(self, on_start, on_stop):
        self._on_start = on_start
        self._on_stop = on_stop

    def set_running(self, running: bool):
        self.start_btn.configure(state="normal" if not running else "disabled")
        self.stop_btn.configure(state="normal" if running else "disabled")
        self.recog_btn.configure(state="normal" if not running else "disabled")
        self.trans_btn.configure(state="normal" if not running else "disabled")
        self._source_option.configure(state="normal" if not running else "disabled")
        self._target_option.configure(state="normal" if not running else "disabled")
