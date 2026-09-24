data "aws_caller_identity" "current" {}
locals {
  iam_policy_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/${var.iam_policy_name}"
}
module "storage" {
  source       = "../../modules/storage"
  project_name = var.project_name
  account_id   = data.aws_caller_identity.current.account_id
}

module "notifications" {
  source       = "../../modules/notifications"
  project_name = var.project_name
  notify_email = var.notify_email
}

module "tts_pipeline" {
  source            = "../../modules/tts-pipeline"
  project_name      = var.project_name
  aws_region        = var.aws_region
  account_id        = data.aws_caller_identity.current.account_id
  input_bucket_id   = module.storage.input_bucket_id
  input_bucket_arn  = module.storage.input_bucket_arn
  output_bucket_id  = module.storage.output_bucket_id
  output_bucket_arn = module.storage.output_bucket_arn
  polly_voice_id    = var.polly_voice_id
  polly_engine      = var.polly_engine
}
##prueba
module "notifier" {
  source            = "../../modules/notifier"
  project_name      = var.project_name
  aws_region        = var.aws_region
  account_id        = data.aws_caller_identity.current.account_id
  output_bucket_id  = module.storage.output_bucket_id
  output_bucket_arn = module.storage.output_bucket_arn
  topic_arn         = module.notifications.topic_arn
}

module "github_oidc" {
  source      = "../../modules/github-oidc"
  github_org  = var.github_org
  github_repo = var.github_repo
  policy_arn  = local.iam_policy_arn
}