terraform-plan: terraform-validate
    cd infra; terraform plan -out=tfplan

terraform-init:
    cd infra; terraform init -backend=true

terraform-validate: terraform-init
    cd infra; terraform validate

terraform-apply: terraform-plan
    cd infra; terraform apply -auto-approve

terraform-format:
    terraform fmt -recursive

terraform-destroy:
    cd infra; terraform destroy

install-function-deps:
    cd lambda/src; pip install -r requirements.txt -t .