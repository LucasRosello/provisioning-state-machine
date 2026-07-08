"""ResolveTemplate: resolve the template to an IMMUTABLE git ref + commit_sha.

Guarantees terraform runs against a pinned version of the template. Demo uses a
static registry; production resolves the tag to a commit via the git provider.
"""
import os

import platform_common as pc

TEMPLATES_COMMIT_SHA = os.environ["TEMPLATES_COMMIT_SHA"]

# template_id -> version -> {git_ref, commit_sha, module_path}
REGISTRY = {
    "dynamodb-table": {
        "1.0.0": {
            "git_ref": "dynamodb-table/v1.0.0",
            "commit_sha": TEMPLATES_COMMIT_SHA,
            "module_path": "templates/dynamodb-table",
        }
    },
    "rds-postgres": {
        "1.0.0": {
            "git_ref": "rds-postgres/v1.0.0",
            "commit_sha": TEMPLATES_COMMIT_SHA,
            "module_path": "templates/rds-postgres",
        }
    },
    "cache-valkey": {
        "1.0.0": {
            "git_ref": "cache-valkey/v1.0.0",
            "commit_sha": TEMPLATES_COMMIT_SHA,
            "module_path": "templates/cache-valkey",
        }
    },
}


def handler(event, _context):
    request_id = event["request_id"]
    request = event["request"]
    template_id = request["template_id"]
    version = request["template_version"]

    versions = REGISTRY.get(template_id)
    if not versions or version not in versions:
        raise ValueError(f"template {template_id}@{version} not found in registry")

    resolved = versions[version]
    template = {
        "id": template_id,
        "version": version,
        "git_ref": resolved["git_ref"],
        "commit_sha": resolved["commit_sha"],
        "module_path": resolved["module_path"],
    }

    pc.audit(request_id, "TEMPLATE_RESOLVED", template)
    return {"template": template}
