import os

# --------------------------
# Cloud Run
# --------------------------

IS_SQLITE = not os.getenv("K_SERVICE")

if IS_SQLITE:

    import sqlite3

    def get_connection():
        conn = sqlite3.connect("reservation.db")
        conn.row_factory = sqlite3.Row
        return conn

    PLACEHOLDER = "?"

# --------------------------
# Local Development
# --------------------------
else:

    from google.cloud.sql.connector import Connector
    import pymysql

    connector = Connector()

    def get_connection():
        return connector.connect(
            os.environ["INSTANCE_CONNECTION_NAME"],
            "pymysql",
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            db=os.environ["DB_NAME"],
            charset="utf8mb4",
            autocommit=False,
        )

    PLACEHOLDER = "%s"