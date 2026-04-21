from datetime import datetime
import flet as ft

from app.database.models.secondary_models import Contact, Message
from app.state import state


def create_chat_tile(
    contact: Contact, text: str, unread_count: int, timestamp: datetime = datetime.now()
):
    c = contact
    avatar = ft.CircleAvatar(
        content=ft.Text(c.name[0].upper(), color=ft.Colors.WHITE),
        bgcolor=ft.Colors.BLUE_GREY_400,
    )

    if c.is_online:
        avatar = ft.Stack(
            [
                avatar,
                ft.Container(
                    width=12,
                    height=12,
                    bgcolor=ft.Colors.GREEN_500,
                    border_radius=6,
                    border=ft.border.all(2, ft.Colors.SURFACE),
                    alignment=ft.alignment.bottom_right,
                    bottom=0,
                    right=0,
                ),
            ]
        )

    time = timestamp.strftime("%m.%d, в %H:%M")

    trailing_controls = [ft.Text(time, size=12, color=ft.Colors.ON_SURFACE_VARIANT)]

    if unread_count > 0:
        trailing_controls.append(
            ft.Container(
                content=ft.Text(
                    str(unread_count),
                    size=11,
                    color=ft.Colors.WHITE,
                    weight=ft.FontWeight.BOLD,
                ),
                bgcolor=ft.Colors.PRIMARY,
                border_radius=10,
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
            )
        )

    title_row = ft.Row(
        [
            ft.Text(c.name, weight=ft.FontWeight.BOLD, size=16),
            ft.Icon(ft.Icons.LOCK, size=14, color=ft.Colors.ON_SURFACE_VARIANT),
        ],
        spacing=4,
    )

    return ft.ListTile(
        leading=avatar,
        title=title_row,
        subtitle=ft.Text(text, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
        trailing=ft.Column(
            trailing_controls, alignment=ft.MainAxisAlignment.CENTER, spacing=4
        ),
    )


def create_message_widjet(pubkey: bytes, msg: Message):
    try:
        text = state.crypto.decrypt_from(
            sender_public_key_bytes=pubkey,
            ciphertext=msg.encrypted_text,
            nonce=msg.nonce,
        )
    except Exception:
        text = "Ошибка расшифровки"
    alignment = (
        ft.MainAxisAlignment.END if msg.is_outbox else ft.MainAxisAlignment.START
    )
    bgcolor = ft.Colors.BLUE_700 if msg.is_outbox else ft.Colors.ON_SURFACE_VARIANT

    return ft.Row(
        [
            ft.Container(
                content=ft.Text(
                    text,
                    color=(ft.Colors.WHITE if msg.is_outbox else ft.Colors.ON_SURFACE),
                ),
                padding=12,
                border_radius=15,
                bgcolor=bgcolor,
                width=600,
            )
        ],
        alignment=alignment,
    )
