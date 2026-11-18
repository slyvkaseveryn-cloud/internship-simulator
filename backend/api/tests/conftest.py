import os
import sys
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.update(TABLE_NAME="test-table", AWS_DEFAULT_REGION="eu-central-1",
                  AWS_ACCESS_KEY_ID="testing", AWS_SECRET_ACCESS_KEY="testing")


@pytest.fixture(autouse=True)
def dynamo():
    """A fresh in-memory DynamoDB table (moto) for every test: no network, no AWS account."""
    from app import db

    with mock_aws():
        boto3.client("dynamodb").create_table(
            TableName="test-table", BillingMode="PAY_PER_REQUEST",
            KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}, {"AttributeName": "sk", "KeyType": "RANGE"}],
            AttributeDefinitions=[{"AttributeName": n, "AttributeType": "S"} for n in ("pk", "sk", "gsi1pk", "gsi1sk")],
            GlobalSecondaryIndexes=[{
                "IndexName": "gsi1", "Projection": {"ProjectionType": "ALL"},
                "KeySchema": [{"AttributeName": "gsi1pk", "KeyType": "HASH"}, {"AttributeName": "gsi1sk", "KeyType": "RANGE"}],
            }],
        )
        db.reset()
        yield boto3.resource("dynamodb").Table("test-table")
        db.reset()
