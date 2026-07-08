"""ExtractOutputs: normalize terraform outputs and strip sensitive values.

Reads outputs.json (terraform output -json) staged by the apply CodeBuild job.
Sensitive outputs are replaced by safe references (e.g. secret_arn) and never
returned as plaintext.
"""
import json
import os

import boto3

import platform_common as pc

_s3 = boto3.client("s3")
ARTIFACTS_BUCKET = os.environ["ARTIFACTS_BUCKET"]


def handler(event, _context):
    request_id = event["request_id"]

    try:
        obj = _s3.get_object(Bucket=ARTIFACTS_BUCKET, Key=f"{request_id}/outputs.json")
        raw = json.loads(obj["Body"].read())
    except _s3.exceptions.NoSuchKey:
        raw = {}

    outputs = {}
    for name, meta in raw.items():
        # terraform output -json => { name: { value, sensitive, type } }
        if meta.get("sensitive"):
            # Keep only safe references; never emit the secret value.
            if name.endswith("secret_arn") or name.endswith("arn"):
                outputs[name] = meta.get("value")
            continue
        outputs[name] = meta.get("value")

    pc.audit(request_id, "OUTPUTS_EXTRACTED", {"keys": list(outputs.keys())})
    return {"resource_outputs": outputs}
