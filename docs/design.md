# Design — states, responsibilities and I/O per stage

The start input is only `{ "request_id": "req-123" }`. Everything else is loaded
from the database. Each state writes its result to a dedicated `ResultPath`, so
the execution state accumulates like this:

```
$.request_id
$.loaded.request        # LoadRequest
$.schema                # ValidateSchema         { valid, errors }
$.ownership             # ValidateOwnership      { valid, errors }
$.policies              # ValidatePolicies       { valid, violations }
$.template              # ResolveTemplate        { id, version, git_ref, commit_sha, module_path }
$.terraform             # GenerateTerraformVariables { module_path, state_key, variables }
$.plan_build            # TerraformPlan (CodeBuild) { build_id, build_status }
$.policy_check          # PolicyCheckPlan        { passed, violations }
$.approval              # EvaluateApproval       { required, approvers, reason }
$.approval_result       # WaitForApproval        { approved, approver }
$.apply_build           # TerraformApply (CodeBuild) { build_id, build_status }
$.resource_outputs      # ExtractOutputs         { outputs }
$.resource              # RegisterResource       { resource_id }
```

## Lambda ↔ state map

| State | Lambda | Reads | Writes (ResultPath) |
|-------|--------|-------|---------------------|
| LoadRequest | `load_request` | `request_id` | `$.loaded.request` |
| ValidateSchema | `validate_schema` | `loaded.request` | `$.schema` |
| ValidateOwnership | `validate_ownership` | `loaded.request` | `$.ownership` |
| ValidatePolicies | `validate_policies` | `loaded.request` | `$.policies` |
| ResolveTemplate | `resolve_template` | `loaded.request` | `$.template` |
| GenerateTerraformVariables | `generate_tfvars` | `loaded.request`, `template` | `$.terraform` |
| TerraformPlan | CodeBuild `terraform-plan` | `template`, `terraform` | `$.plan_build` |
| PolicyCheckPlan | `policy_check_plan` | S3 `tfplan.json` | `$.policy_check` |
| EvaluateApproval | `evaluate_approval` | `loaded.request`, `policy_check` | `$.approval` |
| WaitForApproval | `wait_for_approval` | `approval`, task token | `$.approval_result` |
| TerraformApply | CodeBuild `terraform-apply` | `template`, `terraform` | `$.apply_build` |
| ExtractOutputs | `extract_outputs` | S3 `outputs.json` | `$.resource_outputs` |
| RegisterResource | `register_resource` | `request`, `template`, `terraform`, `resource_outputs` | `$.resource` |
| NotifySuccess | `notify_success` | `resource`, `resource_outputs` | `$.notify` |
| RejectRequest | `reject_request` | full state | `$.rejection` |
| HandleFailure | `handle_failure` | full state | `$.failure` |
| NotifyRejection / NotifyFailure | `notify_failure` | full state | `$.notify` |

## Per-state contracts

### 1. LoadRequest
Loads the request row from DynamoDB. Sets request → `VALIDATING`, emits
`REQUEST_LOADED` + `VALIDATION_STARTED`.
- **In:** `{ "request_id": "req-123" }`
- **Out:** `{ "request": { template_id, template_version, service_name, team, environment, config } }`

### 2. ValidateSchema
Validates required top-level fields and the per-template required config keys and
types.
- **Out (valid):** `{ "schema_valid": true, "errors": [] }`
- **Out (invalid):** `{ "schema_valid": false, "errors": [ { "field": "config.partition_key", "message": "partition_key is required" } ] }`

### 3. ValidateOwnership
Validates that `team` owns `service_name`. Demo uses a local map; production
integrates Backstage / CMDB / GitHub Teams / internal catalog.
- **Out:** `{ "ownership_valid": true|false, "errors": [...] }`

### 4. ValidatePolicies
Cheap platform rules **before** plan: allowed environment, active template,
naming convention, and early guards (e.g. prod RDS must declare backups).
- **Out:** `{ "policies_valid": true|false, "violations": [...] }`

### 5. ResolveTemplate
Resolves `template_id@version` to an **immutable** ref so Terraform runs against
a pinned commit.
- **Out:** `{ "template": { id, version, git_ref, commit_sha, module_path } }`

### 6. GenerateTerraformVariables
Builds the platform-controlled variables (+ mandatory tags), computes a
collision-free `state_key`, and stages `terraform.tfvars.json` in
`s3://<artifacts>/<request_id>/`. Sets request → `PLANNING`.
- **Out:** `{ "terraform": { module_path, state_key, variables } }`

### 7. TerraformPlan (CodeBuild `.sync`)
Clones the repo at `commit_sha`, `terraform init` + `plan`, exports `tfplan` and
`tfplan.json` to the artifacts bucket.
- **Out:** `{ "plan_build": { build_id, build_status } }` (plan artifact in S3)

### 8. PolicyCheckPlan
Evaluates policies (OPA/Conftest, checkov, tfsec) over `tfplan.json`.
- **Out (ok):** `{ "policy_check": { "passed": true, "violations": [] } }`
- **Out (reject):** `{ "policy_check": { "passed": false, "violations": [ { "policy": "prod-rds-backup-required", "message": "..." } ] } }`

### 9. EvaluateApproval
Decides if human approval is required (prod, sensitive template, prod relational
DB, etc.).
- **Out:** `{ "approval": { required, approvers, reason } }`

### 10. WaitForApproval (callback / task token)
Persists the task token on the request, sets request → `WAITING_APPROVAL`, and
pauses until an external approver resumes the execution. Demo auto-approves.
- **Out:** `{ "approval_result": { "approved": true, "approver": "..." } }`

### 11. TerraformApply (CodeBuild `.sync`)
Same commit, same `state_key`, applies the approved `tfplan`. Exports
`outputs.json`. Sets request → `APPLYING`.
- **Out:** `{ "apply_build": { build_id, build_status } }`

### 12. ExtractOutputs
Normalizes `terraform output -json`, drops sensitive values, keeps only safe
references (e.g. `secret_arn`).
- **Out:** `{ "resource_outputs": { table_name, table_arn, ... } }`

### 13. RegisterResource
Writes the resource instance row (`resource_id`, `request_id`, template,
`commit_sha`, team/service/env, `terraform_state_key`, outputs, status). Sets
request → `SUCCEEDED`.
- **Out:** `{ "resource_id": "res-..." }`

### 14. NotifySuccess
Emits `PROVISIONING_SUCCEEDED`, publishes to SNS (portal/MCP/Slack fan-out).

### 15. NotifyFailure / NotifyRejection
Publishes a clear message: `request_id`, final status, error type, detail link,
recommended action.

### 16. RejectRequest
Business rejection. Derives the reason (schema/ownership/policy/plan-policy/
approval), sets request → `REJECTED`, emits `REQUEST_REJECTED`.

### 17. HandleFailure
Global error handler. Classifies the error, distinguishes `FAILED` vs
`INCONSISTENT` (partial apply), records metadata + `PROVISIONING_FAILED`.
