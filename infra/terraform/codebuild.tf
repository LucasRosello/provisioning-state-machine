resource "aws_cloudwatch_log_group" "codebuild_plan" {
  name              = "/aws/codebuild/${var.name_prefix}-terraform-plan"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "codebuild_apply" {
  name              = "/aws/codebuild/${var.name_prefix}-terraform-apply"
  retention_in_days = var.log_retention_days
}

locals {
  codebuild_env = {
    ARTIFACTS_BUCKET   = aws_s3_bucket.artifacts.bucket
    TF_STATE_BUCKET    = aws_s3_bucket.tf_state.bucket
    TF_LOCK_TABLE      = aws_dynamodb_table.tf_locks.name
    TEMPLATES_REPO_URL = var.templates_repo_url
    REQUESTS_TABLE     = aws_dynamodb_table.requests.name
    AUDIT_TABLE        = aws_dynamodb_table.audit_events.name
    AWS_REGION_NAME    = var.aws_region
  }
}

resource "aws_codebuild_project" "terraform_plan" {
  name         = "${var.name_prefix}-terraform-plan"
  description  = "Checks out templates at commit_sha, runs terraform init + plan, uploads tfplan.json."
  service_role = aws_iam_role.codebuild.arn

  artifacts {
    type = "NO_ARTIFACTS"
  }

  environment {
    compute_type    = "BUILD_GENERAL1_SMALL"
    image           = "aws/codebuild/amazonlinux2-x86_64-standard:5.0"
    type            = "LINUX_CONTAINER"
    privileged_mode = false

    dynamic "environment_variable" {
      for_each = local.codebuild_env
      content {
        name  = environment_variable.key
        value = environment_variable.value
      }
    }
  }

  source {
    type      = "NO_SOURCE"
    buildspec = file("${path.module}/../buildspecs/terraform-plan.yml")
  }

  logs_config {
    cloudwatch_logs {
      group_name = aws_cloudwatch_log_group.codebuild_plan.name
    }
  }
}

resource "aws_codebuild_project" "terraform_apply" {
  name         = "${var.name_prefix}-terraform-apply"
  description  = "Checks out templates at the same commit_sha, runs terraform apply against the approved plan."
  service_role = aws_iam_role.codebuild.arn

  artifacts {
    type = "NO_ARTIFACTS"
  }

  environment {
    compute_type    = "BUILD_GENERAL1_SMALL"
    image           = "aws/codebuild/amazonlinux2-x86_64-standard:5.0"
    type            = "LINUX_CONTAINER"
    privileged_mode = false

    dynamic "environment_variable" {
      for_each = local.codebuild_env
      content {
        name  = environment_variable.key
        value = environment_variable.value
      }
    }
  }

  source {
    type      = "NO_SOURCE"
    buildspec = file("${path.module}/../buildspecs/terraform-apply.yml")
  }

  logs_config {
    cloudwatch_logs {
      group_name = aws_cloudwatch_log_group.codebuild_apply.name
    }
  }
}
