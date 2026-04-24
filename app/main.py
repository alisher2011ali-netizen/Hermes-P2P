import flet as ft

from app.ui.router import UIRouter
from app.core.engine import AppEngine
from app.network.network_manager import network_manager


async def main(page: ft.Page):
    engine = AppEngine()
    await engine.initialize_system()

    await network_manager.start_polling()

    page.theme = ft.Theme(
        page_transitions=ft.PageTransitionsTheme(
            android=ft.PageTransitionTheme.NONE,
            ios=ft.PageTransitionTheme.NONE,
            windows=ft.PageTransitionTheme.NONE,
            linux=ft.PageTransitionTheme.NONE,
        )
    )
    page.on_close = network_manager.stop()

    ui = UIRouter(page)
    await ui.build_ui()


if __name__ == "__main__":
    ft.run(main=main)
