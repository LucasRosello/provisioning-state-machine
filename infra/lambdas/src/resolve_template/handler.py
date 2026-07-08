"""ResolveTemplate: resolve the template to an IMMUTABLE git ref + commit_sha.

Guarantees terraform runs against a pinned version of the template. Demo uses a
static registry; production resolves the tag to a commit via the git provider.
"""
import platform_common as pc

# template_id -> version -> {git_ref, commit_sha, module_path}
REGISTRY = {
    "dynamodb-table": {
        "1.0.0": {
            "git_ref": "dynamodb-table/v1.0.0",
            "commit_sha": "abc123def4567890abc123def4567890abc123de",
            "module_path": "templates/dynamodb-table",
        }
    },
    "rds-postgres": {
        "1.0.0": {
            "git_ref": "rds-postgres/v1.0.0",
            "commit_sha": "def456abc7890123def456abc7890123def456ab",
            "module_path": "templates/rds-postgres",
        }
    },
    "cache-valkey": {
        "1.0.0": {
            "git_ref": "cache-valkey/v1.0.0",
            "commit_sha": "0123abc456def7890123abc456def7890123abc4",
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
