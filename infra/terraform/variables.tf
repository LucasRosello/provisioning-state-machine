variable "aws_region" {
  description = "AWS region to deploy the provisioning orchestrator into."
  type        = string
  default     = "us-east-1"
}

variable "name_prefix" {
  description = "Prefix applied to all resource names."
  type        = string
  default     = "platform-provisioning"
}

variable "environment" {
  description = "Environment where the orchestrator itself runs (not the environment of provisioned resources)."
  type        = string
  default     = "dev"
}

variable "templates_repo_url" {
  description = "Git URL of the platform-resource-templates repository that CodeBuild checks out at an immutable commit_sha."
  type        = string
  default     = "https://github.com/LucasRosello/platform-resource-templates.git"
}

variable "templates_commit_sha" {
  description = "Immutable commit SHA in the templates repository used by the demo registry."
  type        = string
  default     = "117861e8861a2f41273e194bd5e3d2dab477dabc"
}

variable "api_repo_url" {
  description = "Git URL of the self-service API repository cloned by the app host."
  type        = string
  default     = "https://github.com/LucasRosello/platform-self-service-api.git"
}

variable "api_repo_ref" {
  description = "Git ref for the API code deployed on the app host."
  type        = string
  default     = "main"
}

variable "portal_repo_url" {
  description = "Git URL of the self-service portal repository cloned by the app host."
  type        = string
  default     = "https://github.com/LucasRosello/platform-self-service-portal.git"
}

variable "portal_repo_ref" {
  description = "Git ref for the portal code deployed on the app host."
  type        = string
  default     = "main"
}

variable "app_instance_type" {
  description = "EC2 instance type used for the demo API and portal host."
  type        = string
  default     = "t3.micro"
}

variable "allowed_http_cidr_blocks" {
  description = "CIDR blocks allowed to reach the demo portal over HTTP."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "lambda_runtime" {
  description = "Runtime for all orchestration Lambdas."
  type        = string
  default     = "python3.12"
}

variable "lambda_timeout_seconds" {
  description = "Default timeout for orchestration Lambdas."
  type        = number
  default     = 30
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention for the state machine, Lambdas and CodeBuild."
  type        = number
  default     = 30
}

variable "notification_email" {
  description = "Optional email subscribed to the notifications SNS topic. Empty disables the subscription."
  type        = string
  default     = ""
}

variable "auto_approve_demo" {
  description = "Demo flag. When true, wait_for_approval auto-approves immediately via SendTaskSuccess instead of pausing for a human callback."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Extra tags merged into every resource."
  type        = map(string)
  default     = {}
}
