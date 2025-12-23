from pathlib import Path


def create_app():
    from dotenv import load_dotenv
    from os import environ
    from os.path import exists, join
    import quart
    from quart_cors import cors  # type: ignore
    import requests
    from inter.blueprints.api import api
    from inter.common import app

    load_dotenv()
    cors(app, allow_origin="http://localhost:5001", allow_credentials=True)
    app.register_error_handler(404, lambda _: ("", 404))
    app.register_error_handler(401, lambda _: ("", 401))

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
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
            response = requests.get(f"http://localhost:5173/{path}")
            return quart.Response(
                response.content,
                response.status_code,
                dict(response.headers.items()),
            )

    app.register_blueprint(api)
    return app
