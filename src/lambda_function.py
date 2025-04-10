import json
import mysql.connector


print(mysql.connector.constants)


def lambda_handler(event, context):
    # TODO implement
    return {
        "statusCode": 200,
        "body": json.dumps("Hello from Lambda! From GitHub Actions!!")
    }
