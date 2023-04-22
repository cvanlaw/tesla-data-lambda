provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Owner      = "cvanlaw/tesla-data-lambda"
      Repository = "https://github.com/cvanlaw/tesla-data-lambda"
    }
  }
}
