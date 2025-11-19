from hashlib import sha256
from http.client import CREATED, OK
from os import environ
import time
import cryptography.hazmat
import cryptography.hazmat.primitives
import cryptography.hazmat.primitives.serialization
import cryptography.x509
import flask
from flask import blueprints
import cryptography


def ntp_now():
    NTP_DELTA = 2208988800
    return int(time.time() + NTP_DELTA)


def create_app():
    ADDRESS = "127.0.0.1"

    app = flask.Flask(__name__)

    @app.route("/")
    def index():
        return flask.render_template("index.html")

    api = flask.Blueprint("api", __name__, url_prefix="/api/v1/")

    @api.route("/")
    def api_index():
        return flask.Response(status=OK)

    @api.route("/stream", methods=["POST", "DELETE"])
    def stream():
        session_id = ntp_now()
        session_version = 0
        unicast_address = ADDRESS
        ufrag = "userfrag"
        pwd = "pwd"

        with open(environ["CERT_PATH"], "rb") as f:
            fingerprint = (
                sha256(
                    cryptography.x509.load_pem_x509_certificate(f.read()).public_bytes(
                        cryptography.hazmat.primitives.serialization.Encoding.DER
                    )
                )
                .digest()
                .hex(":")
                .upper()
            )
        answer = [
            ("v", "0"),
            ("o", f"- {session_id} {session_version} IN IP4 {unicast_address}"),
            ("s", f"session name; {session_id}"),
            ("t", "0 0"),
            ("a", "recvonly"),
            ("a", f"ice-ufrag:{ufrag}"),
            ("a", f"ice-pwd:{pwd}"),
            ("a", f"fingerprint:sha-256 {fingerprint}"),
            ("a", "setup:passive"),
            ("m", "video 5001 RTP/AVP 96 97"),
        ]
        answer = "".join(f"{key}={value}\r\n" for key, value in answer)
        print(answer)
        location = f"http://{ADDRESS}:5001/api/v1/stream/0"
        return flask.Response(
            answer,
            content_type="application/sdp",
            status=CREATED,
            headers={"Location": location},
        )

    @api.route("/stream/0", methods=["GET", "POST", "PATCH"])
    def stream_session():
        print("a")
        print(flask.request.__dict__)
        return flask.Response(status=200)

    @api.route("/stream/0", methods=["DELETE"])
    def stream_delete():
        print("deleting stream")
        return flask.Response(status=200)

    app.register_blueprint(api)
    return app
