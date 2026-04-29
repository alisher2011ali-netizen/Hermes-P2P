from datetime import datetime
import flet as ft
import asyncio

from app.database.repositories import messages
from app.database.models import Account, Contact, Message
from app.state import state


def build_login_view(
    accounts_list, login_container: ft.Column, on_account_click, on_create_new_click
):
    login_container.controls.clear()

    acc: Account
    for acc in accounts_list:
        login_container.controls.append(
            ft.ListTile(
                title=ft.Text(acc.display_name),
                leading=ft.Icon(ft.Icons.PERSON),
                on_click=lambda _: asyncio.create_task(
                    on_account_click(acc.display_name)
                ),
            )
        )

    login_container.controls.append(
        ft.TextButton(
            "Создать новый профиль", on_click=lambda _: on_create_new_click("/sign-up")
        )
    )

    return ft.View(
        route="/",
        controls=[
            ft.AppBar(
                title=ft.Text("Выберите аккаунт"), bgcolor=ft.Colors.ON_SURFACE_VARIANT
            ),
            ft.Container(content=login_container, padding=20),
        ],
    )


def build_password_step(container: ft.Column, name: str, on_confirm, on_back):
    pass_input = ft.TextField(
        label="Введите пароль",
        password=True,
        can_reveal_password=True,
        width=300,
        autofocus=True,
    )

    container.controls.extend(
        [
            ft.Text(f"Вход в аккаунт: {name}", size=20, weight="bold"),
            pass_input,
            ft.ElevatedButton(
                "Войти", on_click=lambda _: asyncio.create_task(on_confirm(pass_input))
            ),
            ft.TextButton("Назад", on_click=on_back),
        ]
    )


def build_sign_up_view(on_register_click, on_back_click, error_text_ref):
    """Return the ready object of class View for registration."""
    name_input = ft.TextField(label="Введите имя", width=300)
    pass_input = ft.TextField(
        label="Введите пароль", password=True, can_reveal_password=True, width=300
    )
    pass_format = ft.Text(
        """Требования к паролю:
    ▪ Не менее 8 символов.
    ▪ Только латинские буквы (A-Z, a-z).
    ▪ Хотя бы одна заглавная буква.
    ▪ Хотя бы одна цифра.
    ▪ Хотя бы один спецсимвол из набора: @ $ ! % * ? &.
    ▪ Без пробелов и русских букв."""
    )

    register_btn = ft.ElevatedButton(
        "Зарегистрироваться",
        on_click=lambda _: asyncio.create_task(
            on_register_click(name_input.value, pass_input.value)
        ),
    )
    back_btn = ft.TextButton("Назад", on_click=lambda _: on_back_click())

    return ft.View(
        route="/sign-up",
        controls=[
            ft.AppBar(
                title=ft.Text("Регистрация"), bgcolor=ft.Colors.ON_SURFACE_VARIANT
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Регистрация в Hermes-P2P", size=20),
                        name_input,
                        pass_input,
                        pass_format,
                        error_text_ref,
                        register_btn,
                        back_btn,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.BASELINE,
                ),
                padding=20,
            ),
        ],
    )


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


def build_chats_view(
    on_add_contact_click, get_nav_bar, chat_list_container, message_view_container
):
    search_field = ft.TextField(
        hint_text="Поиск контактов...",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=20,
        height=45,
        content_padding=10,
        on_change=lambda _: print("Ищем"),
    )

    content = ft.Row(
        expand=True,
        spacing=0,
        controls=[
            ft.Container(
                width=350,
                content=ft.Column(
                    [
                        ft.Container(
                            ft.Row(
                                [
                                    search_field,
                                    ft.IconButton(
                                        icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                                        on_click=lambda _: on_add_contact_click(
                                            "/add-contact"
                                        ),
                                    ),
                                ]
                            ),
                            padding=ft.padding.only(right=5),
                        ),
                        chat_list_container,
                    ],
                ),
                border=ft.border.only(
                    right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
                ),
            ),
            ft.Container(expand=True, content=message_view_container),
        ],
    )
    return ft.View(
        route="/chats",
        controls=[
            ft.AppBar(
                title=ft.Text("Hermes-P2P", weight="bold"),
                center_title=False,
                actions=[
                    ft.IconButton(
                        ft.Icons.SETTINGS, on_click=lambda _: print("Настройки")
                    )
                ],
            ),
            content,
        ],
        navigation_bar=get_nav_bar(0),
    )


async def create_message_widjet(
    text: str = None,
    is_outbox: bool = None,
):
    alignment = ft.MainAxisAlignment.END if is_outbox else ft.MainAxisAlignment.START
    bgcolor = ft.Colors.BLUE_700 if is_outbox else ft.Colors.GREY_300
    text_color = ft.Colors.WHITE if is_outbox else ft.Colors.ON_SURFACE

    return ft.Row(
        [
            ft.Container(
                content=ft.Text(text, color=text_color),
                padding=12,
                border_radius=15,
                bgcolor=bgcolor,
                max_width=600,
            )
        ],
        alignment=alignment,
    )
