"""识别与翻译页面：控制区、显示区、一键清空、DisplayTarget 预留"""
import customtkinter as ctk

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
            border_color="#e5e7eb",
        )
        ctrl_card.pack(fill="x", pady=(0, 16))
        ctrl_frame = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=20, pady=16)

        self.recog_var = ctk.BooleanVar(value=True)
        self.trans_var = ctk.BooleanVar(value=True)
        self.recog_cb = ctk.CTkCheckBox(
            ctrl_frame,
            text="识别",
            variable=self.recog_var,
            text_color=TEXT_BODY,
            border_color=BTN_SECONDARY_BORDER,
        )
        self.recog_cb.pack(side="left", padx=(0, 24))
        self.trans_cb = ctk.CTkCheckBox(
            ctrl_frame,
            text="翻译",
            variable=self.trans_var,
            text_color=TEXT_BODY,
            border_color=BTN_SECONDARY_BORDER,
        )
        self.trans_cb.pack(side="left", padx=(0, 24))

        self.start_btn = ctk.CTkButton(
            ctrl_frame,
            text="开始",
            command=self._on_start_click,
            width=88,
            height=36,
            corner_radius=BTN_RADIUS,
            fg_color=ACCENT,
            hover_color="#1d4ed8",
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

        # 显示区（卡片）
        display_card = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=CARD_RADIUS,
            border_width=1,
            border_color="#e5e7eb",
        )
        display_card.pack(fill="both", expand=True)
        inner = ctk.CTkFrame(display_card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=16)
        self.textbox = ctk.CTkTextbox(
            inner,
            wrap="word",
            font=ctk.CTkFont(size=14),
            fg_color="#fafafa",
            border_width=1,
            border_color="#e5e7eb",
            corner_radius=INPUT_RADIUS,
            text_color=TEXT_BODY,
        )
        self.textbox.pack(fill="both", expand=True)
        self._display = TextboxDisplayTarget(self.textbox)

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

    def get_display_target(self) -> DisplayTarget | None:
        return self._display

    def set_callbacks(self, on_start, on_stop):
        self._on_start = on_start
        self._on_stop = on_stop

    def set_running(self, running: bool):
        self.start_btn.configure(state="normal" if not running else "disabled")
        self.stop_btn.configure(state="normal" if running else "disabled")
        self.recog_cb.configure(state="normal" if not running else "disabled")
        self.trans_cb.configure(state="normal" if not running else "disabled")
