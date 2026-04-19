import flet as ft

from app.ui.router import UIRouter
from app.core.engine import AppEngine


async def main(page: ft.Page):
    engine = AppEngine()

    await engine.initialize_system()

    ui = UIRouter(page)
    await ui.build_ui()


if __name__ == "__main__":
    ft.run(main=main)
