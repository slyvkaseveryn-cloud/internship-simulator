import json

from app.handler import handler

STUDENT = {"sub": "u-student", "email": "olya@example.org", "cognito:groups": ""}
REVIEWER = {"sub": "u-rev", "email": "rev@example.org", "cognito:groups": "[reviewers]"}


def call(method, path, claims=None, body=None, anon=None):
    ctx = {"http": {"method": method}}
    if claims:
        ctx["authorizer"] = {"jwt": {"claims": claims}}
    event = {"rawPath": path, "requestContext": ctx, "headers": {"x-anon-id": anon} if anon else {},
             "body": json.dumps(body) if body is not None else None}
    r = handler(event, None)
    return r["statusCode"], json.loads(r["body"])


def events(table, name=None):
    items = table.query(KeyConditionExpression="pk = :p", ExpressionAttributeValues={":p": "EVENT"})["Items"]
    return [i for i in items if name is None or i["event"] == name]
