import flet as ft
import asyncio

from app.state import state
from app.services.auth_service import AuthService
from app.database.manager import main_session_factory
from app.database.repositories import accounts, contacts
from app.ui import provider
from app.utils import re_validation


class UIRouter:

    def __init__(self, page: ft.Page):
        self.page = page
        self.auth_service = AuthService()
        self.login_container = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    async def build_ui(self):
        self.page.title = "Hermes-P2P"
        self.page.on_route_change = self.route_change

        await self.route_change(None)

        self.page.go("/")

    async def route_change(self, e):
        self.page.views.clear()

        match self.page.route:
            case "/":
                view = await self.get_login_view()
            case "/sign-up":
                view = await self.get_sign_up_view()
            case "/chats":
                view = await self.get_chats_view()
            case _:
                view = ft.View("/", [ft.Text("404 - Страница не найдена")])

        self.page.views.append(view)
        self.page.update()

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

        content = ft.ListView(expand=True, spacing=0, divider_thickness=0.5)

        async with state.session_factory() as session:
            data_list = await contacts.get_contacts_with_last_message(session)

        for data in data_list:
            tile = await provider.get_chat_tile(data)
            content.controls.append(tile)

        return ft.View(
            route="/chats",
            controls=[
                ft.AppBar(
                    title=ft.Text("Hermes-P2P", weight="bold"),
                    bgcolor=ft.Colors.ON_SURFACE_VARIANT,
                    center_title=False,
                    actions=[
                        ft.IconButton(
                            ft.Icons.SETTINGS, on_click=lambda _: print("Настройки")
                        )
                    ],
                ),
                search_field,
                content,
            ],
            floating_action_button=ft.FloatingActionButton(
                icon=ft.Icons.ADD,
                bgcolor=ft.Colors.PRIMARY_CONTAINER,
                on_click=lambda _: asyncio.create_task(),
            ),
        )
