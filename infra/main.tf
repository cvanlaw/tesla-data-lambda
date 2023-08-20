locals {
  lambda_function_name = "tesla-data-exporter"
}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# See also the following AWS managed policy: AWSLambdaBasicExecutionRole
data "aws_iam_policy_document" "lambda" {
  statement {
    effect = "Allow"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      aws_cloudwatch_log_group.this.arn, "${aws_cloudwatch_log_group.this.arn}*"
    ]
  }
  statement {
    effect = "Allow"

    actions = [
      "s3:PutObject*"
    ]

    resources = [
      "${aws_s3_bucket.this.arn}*"
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "ssm:DescribeParameters",
      "ssm:GetParameter"
    ]
    resources = [
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/${local.lambda_function_name}/*"
    ]
  }
}

resource "aws_s3_bucket" "this" {
  bucket_prefix = local.lambda_function_name
}

resource "aws_iam_policy" "lambda" {
  name        = local.lambda_function_name
  path        = "/"
  description = "IAM policy for ${local.lambda_function_name}"
  policy      = data.aws_iam_policy_document.lambda.json
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.this.name
  policy_arn = aws_iam_policy.lambda.arn
}

resource "aws_iam_role" "this" {
  name               = local.lambda_function_name
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

data "archive_file" "this" {
  type        = "zip"
  source_dir  = "../lambda/src"
  output_path = "lambda.zip"
}

resource "aws_lambda_function" "this" {
  function_name    = local.lambda_function_name
  package_type     = "Zip"
  handler          = "function.handler"
  runtime          = "python3.10"
  filename         = data.archive_file.this.output_path
  source_code_hash = data.archive_file.this.output_base64sha256
  memory_size      = var.memory_size
  timeout          = var.timeout_seconds
  role             = aws_iam_role.this.arn

  environment {
    variables = {
      BUCKET_NAME             = aws_s3_bucket.this.bucket
      EMAIL_SSM_PARAM_NAME    = aws_ssm_parameter.email.name
      REFRESH_TOKEN_SSM_PARAM = aws_ssm_parameter.refresh_token.name
    }
  }
}

resource "aws_cloudwatch_log_group" "this" {
  name              = "/aws/lambda/${local.lambda_function_name}"
  retention_in_days = 14
}

resource "aws_ssm_parameter" "email" {
  name  = "/${local.lambda_function_name}/email"
  type  = "String"
  value = "placeholder"

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "refresh_token" {
  name  = "/${local.lambda_function_name}/refresh_token"
  type  = "String"
  value = "placeholder"

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_cloudwatch_event_rule" "this" {
  name_prefix         = local.lambda_function_name
  schedule_expression = "rate(8 hours)"
}

resource "aws_cloudwatch_event_target" "this" {
  rule = aws_cloudwatch_event_rule.this.name
  arn  = aws_lambda_function.this.arn
}

resource "aws_lambda_permission" "cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.this.arn
}
