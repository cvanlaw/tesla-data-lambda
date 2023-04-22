terraform-plan: terraform-validate
    cd infra; terraform plan -out=tfplan

terraform-init:
    cd infra; terraform init -backend=true

terraform-validate: terraform-init
    cd infra; terraform validate

terraform-apply: terraform-plan
    cd infra; terraform apply tfplan

terraform-format:
    terraform fmt -recursive