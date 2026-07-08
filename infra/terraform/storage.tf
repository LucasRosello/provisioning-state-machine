data "aws_caller_identity" "current" {}

# ---------------------------------------------------------------------------
# DynamoDB: source of truth for requests, provisioned resources and audit log
# ---------------------------------------------------------------------------

resource "aws_dynamodb_table" "requests" {
  name         = "${var.name_prefix}-requests"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "request_id"

  attribute {
    name = "request_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }
}

resource "aws_dynamodb_table" "resource_instances" {
  name         = "${var.name_prefix}-resource-instances"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "resource_id"

  attribute {
    name = "resource_id"
    type = "S"
  }

  attribute {
    name = "request_id"
    type = "S"
  }

  global_secondary_index {
    name            = "by-request"
    hash_key        = "request_id"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }
}

resource "aws_dynamodb_table" "audit_events" {
  name         = "${var.name_prefix}-audit-events"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "request_id"
  range_key    = "event_id"

  attribute {
    name = "request_id"
    type = "S"
  }

  attribute {
    name = "event_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }
}

# Terraform state lock table used by CodeBuild for the *provisioned* resources.
resource "aws_dynamodb_table" "tf_locks" {
  name         = "${var.name_prefix}-tf-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  server_side_encryption {
    enabled = true
  }
}

# ---------------------------------------------------------------------------
# S3: plan artifacts and terraform remote state for provisioned resources
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "artifacts" {
  bucket = "${var.name_prefix}-artifacts-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket" "tf_state" {
  bucket = "${var.name_prefix}-tfstate-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "tf_state" {
  bucket                  = aws_s3_bucket.tf_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
