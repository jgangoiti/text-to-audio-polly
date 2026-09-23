variable "github_org" {
  description = "Organización o usuario de GitHub, ej. 'jgangoiti'"
  type        = string
}

variable "github_repo" {
  description = "Nombre del repo, ej. 'text-to-audio-polly'"
  type        = string
}

variable "allowed_branch" {
  description = "Rama que puede aplicar cambios (además de todas poder hacer plan en PR). Usa '*' para no restringir."
  type        = string
  default     = "main"
}

variable "policy_arn" {
  description = "ARN de la policy de mínimo privilegio a adjuntar al rol (la misma que ya usas para jon-terraform)"
  type        = string
}
