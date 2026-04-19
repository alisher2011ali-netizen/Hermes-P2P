import flet as ft

from app.ui.router import UIRouter
from app.core.engine import AppEngine


async def main(page: ft.Page):
    engine = AppEngine()

    await engine.initialize_system()

    page.theme = ft.Theme(
        page_transitions=ft.PageTransitionsTheme(
            android=ft.PageTransitionTheme.NONE,
            ios=ft.PageTransitionTheme.NONE,
            windows=ft.PageTransitionTheme.NONE,
            linux=ft.PageTransitionTheme.NONE,
        )
    )

    ui = UIRouter(page)
    await ui.build_ui()


if __name__ == "__main__":
    ft.run(main=main)
