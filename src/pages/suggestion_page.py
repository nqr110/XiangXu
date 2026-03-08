"""对话建议页面（占位）"""
import customtkinter as ctk

from src.theme import BG_CARD, BORDER_COLOR, CARD_RADIUS, TEXT_MUTED


class SuggestionPage(ctk.CTkFrame):
    """对话建议页面，显示占位文案"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._build_ui()

    def _build_ui(self):
        self.configure(fg_color="transparent")
        card = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=CARD_RADIUS,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.6, relheight=0.35)
        label = ctk.CTkLabel(
            card,
            text="正在施工，敬请期待",
            font=ctk.CTkFont(size=18),
            text_color=TEXT_MUTED,
        )
        label.place(relx=0.5, rely=0.5, anchor="center")
