data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "app" {
  name               = "${var.name_prefix}-app-host"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

data "aws_iam_policy_document" "app" {
  statement {
    sid       = "StartProvisioningWorkflow"
    effect    = "Allow"
    actions   = ["states:StartExecution"]
    resources = [aws_sfn_state_machine.provisioning.arn]
  }

  statement {
    sid     = "ReadWorkflowExecutions"
    effect  = "Allow"
    actions = ["states:DescribeExecution"]
    resources = [
      "arn:aws:states:${var.aws_region}:${data.aws_caller_identity.current.account_id}:execution:${aws_sfn_state_machine.provisioning.name}:*",
    ]
  }

  statement {
    sid    = "WriteRequestsAndAudit"
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:Scan",
      "dynamodb:Query",
    ]
    resources = [
      aws_dynamodb_table.requests.arn,
      aws_dynamodb_table.audit_events.arn,
    ]
  }
}

resource "aws_iam_role_policy" "app" {
  name   = "${var.name_prefix}-app-host"
  role   = aws_iam_role.app.id
  policy = data.aws_iam_policy_document.app.json
}

resource "aws_iam_instance_profile" "app" {
  name = "${var.name_prefix}-app-host"
  role = aws_iam_role.app.name
}

resource "aws_security_group" "app" {
  name        = "${var.name_prefix}-app-host"
  description = "HTTP access for the self-service demo portal"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = var.allowed_http_cidr_blocks
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "app" {
  ami                         = data.aws_ami.amazon_linux_2023.id
  instance_type               = var.app_instance_type
  subnet_id                   = data.aws_subnets.default.ids[0]
  vpc_security_group_ids      = [aws_security_group.app.id]
  iam_instance_profile        = aws_iam_instance_profile.app.name
  associate_public_ip_address = true
  user_data_replace_on_change = true

  user_data = templatefile("${path.module}/user-data.sh.tftpl", {
    api_repo_url      = var.api_repo_url
    api_repo_ref      = var.api_repo_ref
    portal_repo_url   = var.portal_repo_url
    portal_repo_ref   = var.portal_repo_ref
    aws_region        = var.aws_region
    state_machine_arn = aws_sfn_state_machine.provisioning.arn
    requests_table    = aws_dynamodb_table.requests.name
    audit_table       = aws_dynamodb_table.audit_events.name
  })

  tags = {
    Name      = "${var.name_prefix}-app-host"
    Component = "api-portal-host"
  }

  depends_on = [
    aws_iam_role_policy.app,
    aws_sfn_state_machine.provisioning,
  ]
}
