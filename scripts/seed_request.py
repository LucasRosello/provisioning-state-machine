#!/usr/bin/env python3
"""Insert a demo request row so the state machine can be started with it.

Usage:
    python scripts/seed_request.py --request-id req-123 \
        --table platform-provisioning-requests --region us-east-1

Then:
    aws stepfunctions start-execution \
        --state-machine-arn <arn> --input '{"request_id":"req-123"}'
"""
import argparse
import datetime

import boto3


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--request-id", required=True)
    p.add_argument("--table", default="platform-provisioning-requests")
    p.add_argument("--region", default="us-east-1")
    p.add_argument("--template-id", default="dynamodb-table")
    p.add_argument("--environment", default="dev")
    args = p.parse_args()

    ddb = boto3.resource("dynamodb", region_name=args.region)
    ddb.Table(args.table).put_item(
        Item={
            "request_id": args.request_id,
            "status": "CREATED",
            "template_id": args.template_id,
            "template_version": "1.0.0",
            "service_name": "users-api",
            "team": "platform",
            "environment": args.environment,
            "config": {
                "table_name": "user-profiles",
                "partition_key": "user_id",
                "billing_mode": "PAY_PER_REQUEST",
            },
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
    )
    print(f"Seeded request {args.request_id} into {args.table}")


if __name__ == "__main__":
    main()
