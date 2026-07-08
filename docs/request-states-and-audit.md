# Request lifecycle & audit events

## Request status transitions

The workflow keeps the `requests` table authoritative. Statuses set by the
Lambdas / CodeBuild jobs:

| Workflow stage | Request status |
|----------------|----------------|
| LoadRequest / ValidateSchema / ValidateOwnership / ValidatePolicies | `VALIDATING` |
| GenerateTerraformVariables / TerraformPlan | `PLANNING` |
| WaitForApproval | `WAITING_APPROVAL` |
| TerraformApply | `APPLYING` |
| RegisterResource | `SUCCEEDED` |
| RejectRequest | `REJECTED` |
| HandleFailure | `FAILED` or `INCONSISTENT` |

```
CREATED ─▶ VALIDATING ─▶ PLANNING ─▶ [WAITING_APPROVAL] ─▶ APPLYING ─▶ SUCCEEDED
                │            │                │                 │
                └────────────┴────────────────┴─────────────────┴─▶ REJECTED (business)
                                                                  └─▶ FAILED / INCONSISTENT (system)
```

`INCONSISTENT` is used when `TerraformApply` started but failed — real
infrastructure may exist and needs reconciliation, so it is never silently
marked `FAILED`.

## Audit events

Appended to the `audit-events` table (`request_id` + sortable `event_id`).
Emitted across the flow:

```
REQUEST_LOADED
VALIDATION_STARTED
SCHEMA_VALIDATION_SUCCEEDED        SCHEMA_VALIDATION_FAILED
OWNERSHIP_VALIDATION_SUCCEEDED     OWNERSHIP_VALIDATION_FAILED
POLICY_VALIDATION_SUCCEEDED        POLICY_VALIDATION_FAILED
TEMPLATE_RESOLVED
TERRAFORM_VARIABLES_GENERATED
TERRAFORM_PLAN_STARTED             TERRAFORM_PLAN_SUCCEEDED / TERRAFORM_PLAN_FAILED
PLAN_POLICY_CHECK_STARTED          PLAN_POLICY_CHECK_SUCCEEDED / PLAN_POLICY_CHECK_FAILED
APPROVAL_REQUIRED                  APPROVAL_APPROVED / APPROVAL_REJECTED
TERRAFORM_APPLY_STARTED            TERRAFORM_APPLY_SUCCEEDED / TERRAFORM_APPLY_FAILED
OUTPUTS_EXTRACTED
RESOURCE_REGISTERED
PROVISIONING_SUCCEEDED            PROVISIONING_FAILED
REQUEST_REJECTED
```

> `TERRAFORM_PLAN_*` / `TERRAFORM_APPLY_*` are emitted from the CodeBuild
> buildspecs (which also flip the request status to `PLANNING`/`APPLYING`); all
> other events come from the Lambdas via `platform_common.audit(...)`.

## Data model (DynamoDB)

- **requests** — PK `request_id`. Full request + `status`, `updated_at`,
  `resource_id`, `approval_task_token`, error/rejection metadata.
- **resource-instances** — PK `resource_id`, GSI `by-request` on `request_id`.
  One row per provisioned resource.
- **audit-events** — PK `request_id`, SK `event_id` (timestamp-prefixed).
- **tf-locks** — Terraform state lock table for the provisioned resources.
