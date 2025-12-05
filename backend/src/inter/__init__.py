from dotenv import load_dotenv
import quart
from quart_cors import cors  # type: ignore
import requests

from inter.blueprints.api import api


def create_app():
    from inter.common import app

    load_dotenv()

    cors(app, allow_origin="http://localhost:5001", allow_credentials=True)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    async def static_files(path: str):
        # if not app.static_folder:
        #     return abort(500)
        # if exists(join(app.static_folder, path)):
        #     return await quart.send_from_directory(app.static_folder, path)  # type: ignore
        # return await quart.send_file(join(app.static_folder, "index.html"))  # type: ignore
        response = requests.get(f"http://localhost:5173/{path}")
        return quart.Response(
            response.content,
            response.status_code,
            dict(response.headers.items()),
        )

    app.register_blueprint(api)
    return app
