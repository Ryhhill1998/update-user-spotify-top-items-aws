import json
import mysql.connector

from settings import Settings

settings = Settings()

conn = mysql.connector.connect(
    host=settings.db_host,
    database=settings.db_name,
    user=settings.db_user,
    password=settings.db_pass
)

cursor = conn.cursor()
cursor.execute("SELECT VERSION();")
version = cursor.fetchone()


def lambda_handler(event, context):
    # TODO implement
    return {
        "statusCode": 200,
        "body": json.dumps({"version": version})
    }
