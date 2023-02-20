
import logging
from flask import Flask
from prometheus_client import start_http_server
from pyfi_server.routes.transactions import app_frontend_transaction

app = Flask(__name__)

def main():
    logging.getLogger().setLevel(logging.INFO)
    start_http_server(8000)

    app.register_blueprint(app_frontend_transaction)

    app.run(
        host="0.0.0.0",
        port=int("9234"),
        debug=False
    )


if __name__ == '__main__':
    main()
