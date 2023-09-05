module "charing_history_exporter_function" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = local.exporter_lambda_function_name
  description   = "Export charging history"
  handler       = "function.handler"
  runtime       = "python3.10"
  publish       = true

  attach_cloudwatch_logs_policy = true
  attach_policy_jsons           = true

  policy_jsons = [
    data.aws_iam_policy_document.history_exporter.json
  ]

  source_path   = "../lambda/src/export_history.py"
  artifacts_dir = "${path.module}/.terraform/lambda_builds"

  store_on_s3 = false

  layers = [
    module.lambda_layer_s3.lambda_layer_arn,
  ]

  environment_variables = {
    BUCKET_NAME             = module.s3_bucket.s3_bucket_arn
    EMAIL_SSM_PARAM_NAME    = aws_ssm_parameter.email.name
    REFRESH_TOKEN_SSM_PARAM = aws_ssm_parameter.refresh_token.name
  }

  allowed_triggers = {
    EveryEightHours = {
      principal  = "events.amazonaws.com"
      source_arn = aws_cloudwatch_event_rule.this.arn
    }
  }
}

module "history_slicer_function" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "history-slicer"
  description   = "Slice charging history"
  handler       = "function.handler"
  runtime       = "python3.10"
  publish       = true

  attach_cloudwatch_logs_policy = true
  attach_policy_jsons           = true

  policy_jsons = [
    data.aws_iam_policy_document.history_slicer.json
  ]

  source_path   = "../lambda/src/slice_history.py"
  artifacts_dir = "${path.module}/.terraform/lambda_builds"

  store_on_s3 = false

  layers = [
    module.lambda_layer_s3.lambda_layer_arn,
  ]

  environment_variables = {
    TABLE_NAME = module.dynamodb_table.name
  }

  allowed_triggers = {
    EveryEightHours = {
      principal  = "events.amazonaws.com"
      source_arn = aws_cloudwatch_event_rule.this.arn
    }
  }
}

module "lambda_layer_s3" {
  source = "terraform-aws-modules/lambda/aws"

  create_layer = true

  layer_name          = "${local.exporter_lambda_function_name}-dependencies"
  description         = "Dependencies for ${local.exporter_lambda_function_name}"
  compatible_runtimes = ["python3.10"]
  artifacts_dir       = "${path.module}/.terraform/lambda_builds"

  source_path = "../lambda/packages"

  store_on_s3 = true
  s3_prefix   = "lambda-builds/"
  s3_bucket   = local.exporter_lambda_function_name
}

module "s3_bucket" {
  source = "terraform-aws-modules/s3-bucket/aws"

  bucket = local.exporter_lambda_function_name
  acl    = "private"

  control_object_ownership = true
  object_ownership         = "ObjectWriter"

  versioning = {
    enabled = true
  }
}

data "aws_iam_policy_document" "history_exporter" {
  statement {
    effect = "Allow"

    actions = [
      "s3:PutObject*",
      "s3:GetObject*"
    ]

    resources = [
      "${module.s3_bucket.s3_bucket_arn}*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "ssm:DescribeParameters",
      "ssm:GetParameter"
    ]
    resources = [
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/${local.exporter_lambda_function_name}/*"
    ]
  }
}

data "aws_iam_policy_document" "history_slicer" {
  statement {
    effect = "Allow"

    actions = [
      "s3:GetObject*"
    ]

    resources = [
      "${module.s3_bucket.s3_bucket_arn}*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:PutItem"
    ]
    resources = [
      module.dynamodb_table.dynamodb_table_arn
    ]
  }
}

resource "aws_ssm_parameter" "email" {
  name  = "/${local.exporter_lambda_function_name}/email"
  type  = "String"
  value = "placeholder"

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "refresh_token" {
  name  = "/${local.exporter_lambda_function_name}/refresh_token"
  type  = "String"
  value = "placeholder"

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_cloudwatch_event_rule" "this" {
  name_prefix         = local.exporter_lambda_function_name
  schedule_expression = "rate(8 hours)"
}

resource "aws_cloudwatch_event_target" "this" {
  rule = aws_cloudwatch_event_rule.this.name
  arn  = module.charing_history_exporter_function.lambda_function_arn
}
