locals {
  lambda_function_name = "tesla-data-exporter"
}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "this" {
  bucket_prefix = local.lambda_function_name
  force_destroy = true
}
