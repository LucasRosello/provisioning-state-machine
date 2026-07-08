output "state_machine_arn" {
  description = "ARN of the provisioning state machine. The self-service API starts executions here with { request_id }."
  value       = aws_sfn_state_machine.provisioning.arn
}

output "state_machine_name" {
  value = aws_sfn_state_machine.provisioning.name
}

output "requests_table" {
  value = aws_dynamodb_table.requests.name
}

output "resource_instances_table" {
  value = aws_dynamodb_table.resource_instances.name
}

output "audit_events_table" {
  value = aws_dynamodb_table.audit_events.name
}

output "artifacts_bucket" {
  value = aws_s3_bucket.artifacts.bucket
}

output "tf_state_bucket" {
  value = aws_s3_bucket.tf_state.bucket
}

output "notifications_topic_arn" {
  value = aws_sns_topic.notifications.arn
}

output "terraform_plan_project" {
  value = aws_codebuild_project.terraform_plan.name
}

output "terraform_apply_project" {
  value = aws_codebuild_project.terraform_apply.name
}

output "portal_url" {
  description = "Public URL for the AWS-hosted demo portal."
  value       = "http://${aws_instance.app.public_dns}"
}

output "api_health_url" {
  description = "Public health endpoint for the AWS-hosted API through Nginx."
  value       = "http://${aws_instance.app.public_dns}/api/health"
}

output "app_public_ip" {
  value = aws_instance.app.public_ip
}
