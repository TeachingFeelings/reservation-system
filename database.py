import os
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