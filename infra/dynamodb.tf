module "dynamodb_table" {
  source = "terraform-aws-modules/dynamodb-table/aws"

  name     = local.slicer_function_name
  hash_key = "timestamp"

  attributes = [
    {
      name = "timestamp"
      type = "N"
    }
  ]
}

module "vehicle_data" {
  source = "terraform-aws-modules/dynamodb-table/aws"

  name     = "vehicle-data"
  hash_key = "timestamp"

  attributes = [
    {
      name = "timestamp"
      type = "N"
    }
  ]
}
