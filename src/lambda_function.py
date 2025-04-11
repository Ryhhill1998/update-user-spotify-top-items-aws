import json
import os
import httpx
import mysql.connector

conn = mysql.connector.connect(
    host=os.environ.get("DB_HOST"),
    database=os.environ.get("DB_NAME"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASS")
)


def get_user_data_from_records(records: list[dict]):
    pass


def lambda_handler(event, context):
    records = event["Records"]

    for record in records:
        print(f"{record = }")
        message = json.loads(record["body"])
        print(f"{message = }")

    client = httpx.AsyncClient()
