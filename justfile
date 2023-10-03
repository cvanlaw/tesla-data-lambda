terraform-plan: terraform-validate
    cd infra; terraform plan -out=tfplan

terraform-init:
    cd infra; terraform init -backend=true

terraform-validate: terraform-init
    cd infra; terraform validate

terraform-apply: terraform-plan
    cd infra; terraform apply -auto-approve tfplan

terraform-format:
    terraform fmt -recursive

terraform-destroy:
    cd infra; terraform destroy

install-function-deps: clean-function-deps
    mkdir ./lambda/packages/python && cd lambda/packages; pip install -r requirements.txt -t python

clean-function-deps:
    rm -rf ./lambda/packages/python