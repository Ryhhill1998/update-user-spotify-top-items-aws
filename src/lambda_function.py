import json
import os
from dataclasses import dataclass
import mysql.connector

conn = mysql.connector.connect(
    host=os.environ.get("DB_HOST"),
    database=os.environ.get("DB_NAME"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASS")
)

cursor = conn.cursor()
cursor.execute("SELECT VERSION();")
version = cursor.fetchone()


@dataclass
class Record:
    body: str


@dataclass
class EventData:
    Records: list[Record]


def lambda_handler(event, context):
    event_data = EventData(**event)

    for record in event_data.Records:
        message = json.loads(record.body)
        print(f"{message = }")

    # TODO implement
    return {
        "statusCode": 200,
        "body": json.dumps({"version": version})
    }
