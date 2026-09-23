resource "aws_s3_bucket" "input" {
  bucket        = "${var.project_name}-input-${data.aws_caller_identity.current.account_id}"
  force_destroy = true
}

resource "aws_s3_bucket" "output" {
  bucket        = "${var.project_name}-output-${data.aws_caller_identity.current.account_id}"
  force_destroy = true
}

data "aws_caller_identity" "current" {}