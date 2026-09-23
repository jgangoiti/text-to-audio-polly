output "role_arn" {
  value       = aws_iam_role.github_actions.arn
  description = "ARN a usar como AWS_ROLE_ARN en el workflow de GitHub Actions"
}
