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
variable "github_owner_id" {
  description = "ID numérico inmutable del owner del repo en GitHub (claim 'repository_owner_id' del token OIDC; para repos creados a partir de julio 2026, GitHub usa este ID en el sub claim en vez del nombre)"
  type        = string
}

variable "github_repo_id" {
  description = "ID numérico inmutable del repo en GitHub (claim 'repository_id' del token OIDC)"
  type        = string
}
