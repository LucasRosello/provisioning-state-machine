resource "aws_cloudwatch_log_group" "sfn" {
  name              = "/aws/vendedlogs/states/${var.name_prefix}-provisioning"
  retention_in_days = var.log_retention_days
}

locals {
  asl_definition = templatefile("${path.module}/statemachine/provisioning.asl.json", {
    load_request_lambda_arn       = aws_lambda_function.fn["load_request"].arn
    validate_schema_lambda_arn    = aws_lambda_function.fn["validate_schema"].arn
    validate_ownership_lambda_arn = aws_lambda_function.fn["validate_ownership"].arn
    validate_policies_lambda_arn  = aws_lambda_function.fn["validate_policies"].arn
    resolve_template_lambda_arn   = aws_lambda_function.fn["resolve_template"].arn
    generate_tfvars_lambda_arn    = aws_lambda_function.fn["generate_tfvars"].arn
    policy_check_plan_lambda_arn  = aws_lambda_function.fn["policy_check_plan"].arn
    evaluate_approval_lambda_arn  = aws_lambda_function.fn["evaluate_approval"].arn
    wait_for_approval_lambda_arn  = aws_lambda_function.fn["wait_for_approval"].arn
    extract_outputs_lambda_arn    = aws_lambda_function.fn["extract_outputs"].arn
    register_resource_lambda_arn  = aws_lambda_function.fn["register_resource"].arn
    reject_request_lambda_arn     = aws_lambda_function.fn["reject_request"].arn
    handle_failure_lambda_arn     = aws_lambda_function.fn["handle_failure"].arn
    notify_success_lambda_arn     = aws_lambda_function.fn["notify_success"].arn
    notify_failure_lambda_arn     = aws_lambda_function.fn["notify_failure"].arn
    terraform_plan_project        = aws_codebuild_project.terraform_plan.name
    terraform_apply_project       = aws_codebuild_project.terraform_apply.name
  })
}

resource "aws_sfn_state_machine" "provisioning" {
  name     = "${var.name_prefix}-provisioning"
  role_arn = aws_iam_role.sfn.arn
  type     = "STANDARD"

  definition = local.asl_definition

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.sfn.arn}:*"
    include_execution_data = true
    level                  = "ALL"
  }

  tracing_configuration {
    enabled = true
  }
}
