# Provisioning State Machine

Main **AWS Step Functions** state machine that orchestrates provisioning of
resources requested from the self-service API. It loads the request, validates
rules, resolves an immutable template, runs Terraform `plan`/`apply` through
CodeBuild, handles approvals, records audit events and leaves the request in a
final state: `SUCCEEDED`, `FAILED` or `REJECTED`.

Everything here is **infrastructure as code (Terraform)** — the state machine,
Lambdas, CodeBuild projects, DynamoDB tables, S3 buckets, SNS and IAM.

The self-service API starts an execution with only the `request_id`; the full
request is loaded from DynamoDB (the DB is the source of truth):

```json
{ "request_id": "req-123" }
```

## Layout

```
provisioning-state-machine/
├── README.md
├── docs/
│   ├── design.md                     # states, responsibilities, I/O per stage
│   ├── state-machine.md              # mermaid diagram + ASL design notes
│   ├── request-states-and-audit.md   # request lifecycle + audit events
│   └── decisions.md                  # design decisions / trade-offs
└── infra/
    ├── terraform/                    # the whole stack as code
    │   ├── state-machine.tf          # aws_sfn_state_machine + templatefile(ASL)
    │   ├── statemachine/provisioning.asl.json   # Amazon States Language definition
    │   ├── lambdas.tf / layer.tf     # 15 Lambdas + shared layer
    │   ├── codebuild.tf              # terraform plan/apply projects
    │   ├── storage.tf                # DynamoDB tables + S3 buckets
    │   ├── iam.tf / notifications.tf / outputs.tf / variables.tf / locals.tf
    │   └── terraform.tfvars.example
    ├── buildspecs/                   # CodeBuild buildspecs for plan/apply
    └── lambdas/
        ├── layers/common/            # platform_common shared package
        └── src/<lambda>/handler.py   # one folder per Lambda
```

## The flow (16 states + terminals)

`LoadRequest → ValidateSchema → ValidateOwnership → ValidatePolicies →
ResolveTemplate → GenerateTerraformVariables → TerraformPlan → PolicyCheckPlan →
EvaluateApproval → [WaitForApproval] → TerraformApply → ExtractOutputs →
RegisterResource → NotifySuccess → Succeeded`

with `RejectRequest` (business rejection) and `HandleFailure` (system error)
branches, both ending in a notification. See [docs/state-machine.md](docs/state-machine.md).

## Deploy

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars   # edit values
terraform init
terraform apply
```

Then create a demo request and start an execution:

```bash
python ../../scripts/seed_request.py --request-id req-123
aws stepfunctions start-execution \
  --state-machine-arn "$(terraform output -raw state_machine_arn)" \
  --input '{"request_id":"req-123"}'
```

`auto_approve_demo = true` (default) makes `WaitForApproval` auto-approve so the
flow runs end to end without a human in the loop. Set it to `false` to exercise
the real task-token callback.

## Requirements

- Terraform >= 1.5, AWS provider ~> 5.40
- AWS credentials with permissions to create the resources in `infra/terraform`
- The templates repo (default: `platform-resource-templates`) reachable by CodeBuild
