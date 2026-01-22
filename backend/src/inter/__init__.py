from logging import getLogger
import logging
from pathlib import Path
from socket import AF_INET, SOCK_DGRAM, socket

import httpx


def create_app():
    from dotenv import load_dotenv
    from os import environ
    from os.path import exists, join
    import quart
    from quart_cors import cors  # type: ignore
    from inter.blueprints.api import api
    from inter.common import app

    load_dotenv()
    cors(
        app,
        allow_origin=[
            "http://localhost:5001",
            *(
                [
                    (
                        lambda socket: f"http://{(
                            socket.connect(("8.8.8.8", 80)),
                            socket.getsockname(),
                        )[1][0]}:5001"
                    )(socket(AF_INET, SOCK_DGRAM))
                ]
                if not environ.get("PROD")
                else []
            ),
        ],
        allow_credentials=True,
    )
    app.register_error_handler(404, lambda _: ("", 404))
    app.register_error_handler(401, lambda _: ("", 401))

    class Filter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
            return not any(
                path in record.getMessage()
                for path in ["/src/", "/node_modules/", ".svelte-kit"]
            )

    getLogger("hypercorn.access").addFilter(filter=Filter())

    @app.route("/", defaults={"path": ""}, methods=["GET", "POST"])
    @app.route("/<path:path>", methods=["GET", "POST"])
    async def static_files(path: str):
        if environ.get("PROD"):
            if not app.static_folder:
                return quart.abort(500)
            if (
                exists(join(app.static_folder, path))
                and Path(join(app.static_folder, path)).is_file()
            ):
                return await quart.send_from_directory(app.static_folder, path)  # type: ignore
            return await quart.send_file(join(app.static_folder, "index.html"))  # type: ignore
        else:
            response = httpx.get(f"http://localhost:5173/{path}")
            return quart.Response(
                response.content,
                response.status_code,
                dict(response.headers.items()),
            )

    app.register_blueprint(api)
    return app
