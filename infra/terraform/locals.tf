locals {
  common_tags = merge(
    {
      ManagedBy   = "terraform"
      Project     = "platform-self-service"
      Component   = "provisioning-orchestrator"
      Environment = var.environment
    },
    var.tags,
  )

  # One entry per orchestration Lambda. The key is both the source directory
  # (infra/lambdas/src/<key>) and the logical id used across the stack.
  lambdas = {
    load_request       = { description = "Load the request row from DynamoDB by request_id." }
    validate_schema    = { description = "Validate request fields and config against the template schema." }
    validate_ownership = { description = "Validate that the team owns the service." }
    validate_policies  = { description = "Validate platform policies before terraform plan." }
    resolve_template   = { description = "Resolve template to an immutable git_ref/commit_sha." }
    generate_tfvars    = { description = "Generate terraform variables and the state key." }
    policy_check_plan  = { description = "Evaluate OPA/Conftest policies over tfplan.json." }
    evaluate_approval  = { description = "Decide whether human approval is required." }
    wait_for_approval  = { description = "Callback task-token approval gate (auto-approves in demo mode)." }
    extract_outputs    = { description = "Normalize terraform outputs and strip secrets." }
    register_resource  = { description = "Register the provisioned resource instance." }
    reject_request     = { description = "Mark the request REJECTED with a reason." }
    handle_failure     = { description = "Classify errors and mark request FAILED/INCONSISTENT." }
    notify_success     = { description = "Notify success to portal/MCP/Slack." }
    notify_failure     = { description = "Notify failure/rejection to portal/MCP/Slack." }
  }

  lambda_env = {
    REQUESTS_TABLE       = aws_dynamodb_table.requests.name
    RESOURCES_TABLE      = aws_dynamodb_table.resource_instances.name
    AUDIT_TABLE          = aws_dynamodb_table.audit_events.name
    ARTIFACTS_BUCKET     = aws_s3_bucket.artifacts.bucket
    TF_STATE_BUCKET      = aws_s3_bucket.tf_state.bucket
    NOTIFICATIONS_TOPIC  = aws_sns_topic.notifications.arn
    TEMPLATES_REPO_URL   = var.templates_repo_url
    TEMPLATES_COMMIT_SHA = var.templates_commit_sha
    AUTO_APPROVE         = tostring(var.auto_approve_demo)
  }
}
