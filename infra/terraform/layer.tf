# Shared code packaged as a Lambda layer so every handler can reuse the same
# DynamoDB / audit / notification helpers without duplicating logic.

data "archive_file" "common_layer" {
  type        = "zip"
  source_dir  = "${path.module}/../lambdas/layers/common"
  output_path = "${path.module}/.build/common-layer.zip"
}

resource "aws_lambda_layer_version" "common" {
  layer_name          = "${var.name_prefix}-common"
  filename            = data.archive_file.common_layer.output_path
  source_code_hash    = data.archive_file.common_layer.output_base64sha256
  compatible_runtimes = [var.lambda_runtime]
  description         = "Shared platform_common package (DynamoDB, audit events, notifications)."
}
