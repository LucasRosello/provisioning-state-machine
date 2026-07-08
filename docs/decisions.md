# Design decisions

**Only `request_id` as input.** The DB is the source of truth. Passing large
payloads between states risks the 256KB state-size limit and state drift; loading
from `request_id` keeps a single authoritative record.

**Standard workflow, not Express.** The flow is long-running (human approval up
to 24h, CodeBuild minutes), needs exactly-once semantics and full execution
history/audit — that is Standard's sweet spot.

**Terraform via CodeBuild `.sync`.** Terraform needs a real filesystem, network
and long runtime — not a good fit for a Lambda. CodeBuild gives that, and the
`.sync` integration pauses the workflow until the build ends. The plan and apply
run against the same immutable `commit_sha` and the same `state_key`.

**Immutable template refs.** `ResolveTemplate` pins `commit_sha`; both builds
`git checkout` that SHA. A moving branch could change infra between plan and
apply — pinning removes that class of drift.

**Plan → policy-check → approve → apply on the same artifact.** Apply consumes
the exact `tfplan` that was policy-checked and approved, so what was reviewed is
what gets applied.

**Approvals via task-token callback.** The correct pattern to pause a Standard
workflow for an external human decision. The token lives on the request row so a
portal/API can resume with `SendTaskSuccess`/`SendTaskFailure`. A demo flag
auto-approves to exercise the happy path.

**Rejection ≠ failure.** Business rejections end in a `Succeed` (`Rejected`)
state; only system errors end in `Fail`. This keeps Step Functions failure
metrics and alarms meaningful.

**`INCONSISTENT` state.** If apply starts and fails, resources may exist. The
failure handler marks `INCONSISTENT` rather than `FAILED` so reconciliation is
explicit.

**Shared Lambda layer.** `platform_common` centralizes DynamoDB access, audit
emission, status transitions and notifications, so 15 small handlers stay
consistent and thin.

**IAM scoping.** Lambda/SFN roles are least-privilege. The CodeBuild role that
actually provisions resources is intentionally broad in this demo (`dynamodb:*`,
`rds:*`, `elasticache:*`, …) — in production, scope it per template/environment
with permission boundaries and per-account roles.

## Not done here (next steps)

- Real OPA/conftest binary invocation in `policy_check_plan` (currently a
  representative in-Lambda rule set + hook for the artifact).
- Approval portal/API that resolves the task token.
- Per-account / per-environment CodeBuild roles and cross-account assume-role.
- EventBridge alarms on `Failed`/`INCONSISTENT` executions.
- Idempotency guard if the API can start two executions for the same request.
