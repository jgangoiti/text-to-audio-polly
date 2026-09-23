variable "aws_region" {
  description = "Región de AWS donde se despliega el proyecto"
  type        = string
  default     = "eu-west-1"
}

variable "notify_email" {
  description = "Email al que SNS notifica cuando el audio está listo"
  type        = string
}

variable "project_name" {
  description = "Prefijo usado para nombrar todos los recursos"
  type        = string
  default     = "text-to-audio"
}

variable "polly_voice_id" {
  description = "Voz de Polly a usar en la síntesis"
  type        = string
  default     = "Lucia" # voz neural en español
}

variable "polly_engine" {
  description = "Motor de Polly: 'standard' o 'neural' "
  type        = string
  default     = "neural"
}
variable "iam_policy_name" {
  description = "Nombre de la policy IAM de mínimo privilegio ya existente en la cuenta"
  type        = string
}
variable "github_org" {
  description = "Organización o usuario de GitHub"
  type        = string
}

variable "github_repo" {
  description = "Nombre del repo en GitHub"
  type        = string
}