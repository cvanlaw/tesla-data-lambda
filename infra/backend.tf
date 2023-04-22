terraform {
  cloud {
    organization = "vanlaw_dev"
    hostname     = "app.terraform.io"

    workspaces {
      name = "tesla-lambda"
    }
  }
}
