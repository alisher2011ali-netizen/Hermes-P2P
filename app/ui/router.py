import flet as ft
import asyncio

from app.state import state
from app.services.auth_service import AuthService
from app.services import contact_service
from app.services.message_service import MessageService
from app.database.manager import main_session_factory
from app.database.repositories import accounts, contacts
from app.database.repositories import messages as messages_repo
from app.database.models.secondary_models import Contact
from app.ui import provider, builder
from app.utils import re_validation
from app.utils import formatting


class UIRouter:

    def __init__(self, page: ft.Page):
        self.page = page
        self.auth_service = AuthService()
        self.login_container = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        self.add_contact_container = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
        self.selected_contact_id = None
        self.current_nav_index = 0

    async def build_ui(self):
        self.page.title = "Hermes-P2P"
        self.page.on_route_change = self.route_change

        await self.route_change(None)

        self.page.go("/")

    async def route_change(self, e):
        self.page.views.clear()

        match self.page.route:
            case "/":
                state.clear()
                view = await self.get_login_view()
            case "/sign-up":
                view = await self.get_sign_up_view()
            case "/chats":
                view = await self.get_chats_view()
            case "/profile":
                view = await self.get_profile_view()
            case "/add-contact":
                view = await self.get_add_contact_view()
            case _:
                view = ft.View("/", [ft.Text("404 - Страница не найдена")])

        self.page.views.append(view)
        self.page.update()

    def _get_nav_bar(self, current_index: int):
        return ft.NavigationBar(
            selected_index=current_index,
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.CHAT_BUBBLE_OUTLINE,
                    selected_icon=ft.Icons.CHAT_BUBBLE,
                    label="Чаты",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.PERSON_OUTLINE,
                    selected_icon=ft.Icons.PERSON,
                    label="Профиль",
                ),
            ],
            on_change=lambda e: asyncio.create_task(
                self._handle_nav_change(e.control.selected_index)
            ),
        )

    async def _handle_nav_change(self, index: int):
        if index == 0:
            self.page.go("/chats")
        elif index == 1:
            self.page.go("/profile")

    async def get_login_view(self):
        """Создает View для экрана логина"""
        self.login_container.controls.clear()

        async with main_session_factory() as session:
            accounts_list = await accounts.get_all_accounts(session)

        if not accounts_list:
            self.page.go("/sign-up")
            return ft.View(route="/", controls=[ft.Text("Перенаправление...")])

        for acc in accounts_list:
            btn = ft.ListTile(
                title=ft.Text(acc.display_name),
                leading=ft.Icon(ft.Icons.PERSON),
                on_click=lambda e, name=acc.display_name: asyncio.create_task(
                    self.show_password_dialog(name)
                ),
            )
            self.login_container.controls.append(btn)

        self.login_container.controls.append(
            ft.TextButton(
                "Создать новый профиль", on_click=lambda _: self.page.go("/sign-up")
            )
        )

        return ft.View(
            route="/",
            controls=[
                ft.AppBar(
                    title=ft.Text("Выберите аккаунт"),
                    bgcolor=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Container(content=self.login_container, padding=20),
            ],
        )

    async def show_password_dialog(self, name: str):
        """Метод для ввода пароля (подменяет содержимое login_container)."""
        pass_input = ft.TextField(label="Введите пароль", password=True, width=300)

        async def confirm_login(e):
            try:
                success = await self.auth_service.login(name, pass_input.value)
                if success:
                    self.page.go("/chats")
            except ValueError as err:
                pass_input.error = str(err)
                self.page.update()

        self.login_container.controls.clear()
        self.login_container.controls.extend(
            [
                ft.Text(f"Вход в: {name}", size=20, weight=ft.FontWeight.BOLD),
                pass_input,
                ft.ElevatedButton("Войти", on_click=confirm_login),
                ft.TextButton("Назад", on_click=lambda _: self.page.go("/")),
            ]
        )
        self.page.update()

    async def get_sign_up_view(self):
        """Метод регистрации пользователя"""
        name_input = ft.TextField(label="Введите имя", width=300)
        pass_input = ft.TextField(label="Введите пароль", password=True, width=300)
        pass_format = ft.Text(
            """Требования к паролю:
    ▪ Не менее 8 символов.
    ▪ Только латинские буквы (A-Z, a-z).
    ▪ Хотя бы одна заглавная буква.
    ▪ Хотя бы одна цифра.
    ▪ Хотя бы один спецсимвол из набора: @ $ ! % * ? &.
    ▪ Без пробелов и русских букв."""
        )
        error_text = ft.Text(color=ft.Colors.RED)

        async def confirm_sign_up(e):
            error_text.value = ""
            self.page.update()

            try:
                if re_validation.is_valid_pass(pass_input.value):
                    success = await self.auth_service.sign_up(
                        name=name_input.value, password=pass_input.value
                    )
                    if success:
                        self.page.go("/chats")
            except ValueError as err:
                error_text.value = str(err)
                self.page.update()

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
                            error_text,
                            ft.ElevatedButton(
                                "Зарегистрироваться", on_click=confirm_sign_up
                            ),
                            ft.TextButton(
                                "Назад", on_click=lambda _: self.page.go("/")
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.BASELINE,
                    ),
                    padding=20,
                ),
            ],
        )

    async def get_chats_view(self):
        """Страница со списком контактов"""
        account_name = state.current_account.name if state.current_account else "Гость"

        search_field = ft.TextField(
            hint_text="Поиск контактов...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=20,
            height=45,
            content_padding=10,
            on_change=lambda e: print("Ищем"),
        )

        chat_list_container = ft.ListView(expand=True, spacing=0, divider_thickness=0.5)

        async with state.session_factory() as session:
            data_list = await contacts.get_contacts_with_last_message(session)

        for data in data_list:
            tile = await provider.get_chat_tile(data)
            tile.on_click = lambda _: asyncio.create_task(
                self.load_chat_history(data[0])
            )
            chat_list_container.controls.append(tile)

        self.message_view_container = ft.Container(
            expand=True,
            content=ft.Column(
                [
                    ft.Text(
                        "Выберите контакт, чтобы начать с ним общение",
                        size=16,
                        color=ft.Colors.GREY_500,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
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
                                            on_click=lambda _: self.page.go(
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
                ft.Container(expand=True, content=self.message_view_container),
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
            navigation_bar=self._get_nav_bar(0),
        )

    async def load_chat_history(self, contact: Contact):
        self.message_view_container.content = ft.ProgressBar(width=200, color="blue")
        self.page.update()

        async with state.session_factory() as session:
            messages = await messages_repo.get_messages_by_contact_id(
                session=session, contact_id=contact.id
            )

        messages_widjets = []
        for msg in messages:
            msg_widjet = await builder.create_message_widjet(
                pubkey=contact.public_key, msg=msg
            )
            messages_widjets.append(msg_widjet)

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
                        width=18,
                        height=18,
                        bgcolor=ft.Colors.GREEN_500,
                        border_radius=6,
                        border=ft.border.all(2, ft.Colors.SURFACE),
                        alignment=ft.alignment.bottom_right,
                        bottom=0,
                        right=0,
                    ),
                ]
            )
        message_input = ft.TextField(
            hint_text="Сообщение...", expand=True, shift_enter=True
        )

        async def on_send_click(e):
            text = message_input.value
            if not text:
                return

            await MessageService.send_message(contact_id=c.id, text=text)

            message_input.value = ""
            new_widget = await builder.create_message_widjet(text, is_outbox=True)
            messages_widjets.append(new_widget)

            self.page.update()

        self.message_view_container.content = ft.Column(
            [
                ft.Container(
                    ft.Row(
                        controls=[avatar, ft.Text(f"{c.name}", weight="bold", size=18)],
                        spacing=10,
                    ),
                    padding=ft.padding.only(left=15, top=5),
                ),
                ft.Divider(),
                ft.ListView(
                    controls=messages_widjets, expand=True, spacing=10, auto_scroll=True
                ),
                ft.Container(
                    ft.Row(
                        [
                            message_input,
                            ft.IconButton(ft.Icons.SEND, on_click=on_send_click),
                        ]
                    ),
                    padding=ft.padding.only(left=5, right=5),
                ),
            ]
        )

        self.page.update()

    async def get_profile_view(self):
        identity = state.current_account

        token = formatting.generate_invite_token(identity.public_key)

        async def copy_token(e):
            await self.page.clipboard.set(token)

            snack = ft.SnackBar(
                content=ft.Text("Токен скопирован! Отправьте его другу."),
                action="Oк",
                duration=2000,
            )
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()

        token_field = ft.TextField(
            value=token,
            label="Ваш токен приглашения",
            read_only=True,
            text_size=12,
            suffix=ft.IconButton(
                icon=ft.Icons.COPY,
                on_click=copy_token,
                tooltip="Копировать",
            ),
        )

        clue = ft.Text(
            "Другу нужно вставить этот код в разделе 'Добавить контакт'",
            size=14,
            weight="w500",
        )

        return ft.View(
            route="/profile",
            navigation_bar=self._get_nav_bar(1),
            controls=[
                ft.AppBar(
                    title=ft.Text("Мой профиль"),
                    bgcolor=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Column(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.CircleAvatar(
                                        content=ft.Text(
                                            identity.name[0].upper(), size=30
                                        ),
                                        radius=50,
                                    ),
                                    ft.Text(identity.name, size=24, weight="bold"),
                                    ft.Text(
                                        identity.bio
                                        or "О себе еще ничего не написано...",
                                        italic=True,
                                        color=ft.Colors.GREY_500,
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            alignment=ft.alignment.Alignment.CENTER,
                            padding=20,
                        ),
                        ft.Divider(),
                        clue,
                        token_field,
                        ft.Divider(),
                        ft.ElevatedButton(
                            "Редактировать профиль",
                            icon=ft.Icons.EDIT,
                            on_click=lambda _: asyncio.create_task(),
                        ),
                        ft.TextButton(
                            "Выйти из аккаунта",
                            icon_color=ft.Colors.RED,
                            on_click=lambda _: self.page.go("/"),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
            ],
        )

    async def get_add_contact_view(self):
        async def paste_token(e):
            token_input.value = await self.page.clipboard.get()

            snack = ft.SnackBar(
                content=ft.Text("Токен вставлен! Нажмите 'Добавить'."),
                action="Oк",
                duration=2000,
            )
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()

        name_input = ft.TextField(label="Имя контакта", width=300)
        token_input = ft.TextField(
            label="Токен приглашения",
            suffix=ft.IconButton(
                icon=ft.Icons.PASTE,
                on_click=paste_token,
                tooltip="Вставить",
            ),
            width=500,
        )
        self.add_contact_container.controls.clear()
        self.add_contact_container.controls.extend(
            [
                name_input,
                token_input,
                ft.ElevatedButton(
                    "Добавить",
                    icon=ft.Icons.ADD,
                    on_click=lambda _: asyncio.create_task(
                        self.show_contact_added_dialog(
                            name_input.value, token_input.value
                        )
                    ),
                ),
                ft.TextButton("Назад", on_click=lambda _: self.page.go("/chats")),
            ],
        )

        return ft.View(
            route="/add-contact",
            controls=[
                ft.AppBar(
                    title="Создание контакта", bgcolor=ft.Colors.ON_SURFACE_VARIANT
                ),
                ft.Container(content=self.add_contact_container, padding=20),
            ],
        )

    async def show_contact_added_dialog(self, name: str, token: str):
        success, error_msg = await contact_service.make_new_contact(
            name=name, token_string=token
        )
        if success:
            self.add_contact_container.controls.clear()
            self.add_contact_container.controls.extend(
                [
                    ft.Text(
                        f"Контакт: {name} успешно добавлен!",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.TextButton(
                        "К чатам",
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda _: self.page.go("/chats"),
                    ),
                ]
            )
            self.page.update()
        else:
            snack = ft.SnackBar(ft.Text(error_msg))
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()
