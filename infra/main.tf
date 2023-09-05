locals {
  exporter_lambda_function_name = "tesla-data-exporter"
  slicer_function_name          = "tde-slicer"
}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "this" {
  bucket_prefix = local.exporter_lambda_function_name
  # force_destroy = true
}
