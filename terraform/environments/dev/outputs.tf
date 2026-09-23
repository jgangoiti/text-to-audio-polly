output "input_bucket_id" {
  value = module.storage.input_bucket_id
}

output "output_bucket_id" {
  value = module.storage.output_bucket_id
}

output "tts_function_name" {
  value = module.tts_pipeline.function_name
}

output "notifier_function_name" {
  value = module.notifier.function_name
}
output "github_actions_role_arn" {
  value       = module.github_oidc.role_arn
}