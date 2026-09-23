resource "aws_iam_role" "notifier_exec" {
  name = "${var.project_name}-notifier-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "notifier_exec" {
  name = "${var.project_name}-notifier-exec-policy"
  role = aws_iam_role.notifier_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "Logs"
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:${var.aws_region}:${var.account_id}:*"
      },
      {
        Sid      = "ReadOutput"
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "${var.output_bucket_arn}/*"
      },
      {
        Sid      = "PublishNotification"
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = var.topic_arn
      }
    ]
  })
}

data "archive_file" "notifier_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../../src/notifier_handler"
  output_path = "${path.module}/build/notifier_handler.zip"
}

resource "aws_lambda_function" "notifier" {
  function_name = "${var.project_name}-notifier"
  role          = aws_iam_role.notifier_exec.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = 15

  filename         = data.archive_file.notifier_zip.output_path
  source_code_hash = data.archive_file.notifier_zip.output_base64sha256

  environment {
    variables = {
      TOPIC_ARN       = var.topic_arn
      URL_EXPIRY_SECS = "3600"
    }
  }
}

resource "aws_lambda_permission" "allow_s3_output" {
  statement_id  = "AllowS3InvokeNotifier"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.notifier.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = var.output_bucket_arn
}

resource "aws_s3_bucket_notification" "output_trigger" {
  bucket = var.output_bucket_id

  lambda_function {
    lambda_function_arn = aws_lambda_function.notifier.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".mp3"
  }

  depends_on = [aws_lambda_permission.allow_s3_output]
}