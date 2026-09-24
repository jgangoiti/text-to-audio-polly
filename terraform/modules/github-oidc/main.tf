# GitHub ya usa este thumbprint desde 2023; si AWS lo pide de nuevo en el
# futuro, se puede regenerar con: openssl s_client -connect token.actions.githubusercontent.com:443
data "aws_caller_identity" "current" {}
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

resource "aws_iam_role" "github_actions" {
  name = "github-actions-${var.github_repo}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            # Desde julio 2026, GitHub usa por defecto el formato "inmutable" en el sub claim
            # para repos nuevos: repo:OWNER@OWNER_ID/REPO@REPO_ID:... en vez de repo:OWNER/REPO:...
            # Permite PRs de cualquier rama (para el plan) y pushes/environments (para el apply).
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_org}@${var.github_owner_id}/${var.github_repo}@${var.github_repo_id}:*"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "least_privilege" {
  role       = aws_iam_role.github_actions.name
  policy_arn = var.policy_arn
}
