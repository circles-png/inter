from asyncio import set_event_loop_policy
from http.client import INTERNAL_SERVER_ERROR, NOT_FOUND, OK, UNAUTHORIZED
from logging import getLogger
import logging
from pathlib import Path
import httpx
from quart import abort, redirect

def create_app():
    from dotenv import load_dotenv

    load_dotenv()
    from os import environ
    from os.path import exists, join
    import quart
    from inter.blueprints.api import api
    from inter.common import app

    app.register_error_handler(NOT_FOUND, lambda _: ("", NOT_FOUND))
    app.register_error_handler(UNAUTHORIZED, lambda _: ("", UNAUTHORIZED))

    class Filter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
            return not any(
                path in record.getMessage()
                for path in ["/src/", "/node_modules/", ".svelte-kit"]
            )

    getLogger("hypercorn.access").addFilter(filter=Filter())

    try:
        import uvloop

        set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        pass

    @app.route("/", defaults={"path": ""}, methods=["GET", "POST"])
    @app.route("/<path:path>", methods=["GET", "POST"])
    async def static_files(path: str):
        if environ.get("PROD"):
            if not app.static_folder:
                return abort(INTERNAL_SERVER_ERROR)
            if (
                exists(join(app.static_folder, path))
                and Path(join(app.static_folder, path)).is_file()
            ):
                return await quart.send_from_directory(app.static_folder, path)  # type: ignore
            return await quart.send_file(join(app.static_folder, "index.html"))  # type: ignore
        else:
            response = httpx.get(f"http://localhost:5173/{path}")
            if response.status_code != OK:
                return redirect("/")
            return quart.Response(
                response.content,
                headers=dict(response.headers.items()),
            )

    app.register_blueprint(api)
    return app
