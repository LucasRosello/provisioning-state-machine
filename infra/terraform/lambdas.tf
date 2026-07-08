data "archive_file" "lambda" {
  for_each    = local.lambdas
  type        = "zip"
  source_dir  = "${path.module}/../lambdas/src/${each.key}"
  output_path = "${path.module}/.build/${each.key}.zip"
}

resource "aws_cloudwatch_log_group" "lambda" {
  for_each          = local.lambdas
  name              = "/aws/lambda/${var.name_prefix}-${replace(each.key, "_", "-")}"
  retention_in_days = var.log_retention_days
}

resource "aws_lambda_function" "fn" {
  for_each = local.lambdas

  function_name    = "${var.name_prefix}-${replace(each.key, "_", "-")}"
  description      = each.value.description
  role             = aws_iam_role.lambda.arn
  handler          = "handler.handler"
  runtime          = var.lambda_runtime
  timeout          = var.lambda_timeout_seconds
  filename         = data.archive_file.lambda[each.key].output_path
  source_code_hash = data.archive_file.lambda[each.key].output_base64sha256
  layers           = [aws_lambda_layer_version.common.arn]

  environment {
    variables = local.lambda_env
  }

  depends_on = [aws_cloudwatch_log_group.lambda]
}
