terraform {
  backend "s3" {
    bucket       = "internship-simulator-tfstate-637965527585"
    key          = "bootstrap/terraform.tfstate"
    region       = "eu-central-1"
    use_lockfile = true
    encrypt      = true
  }
}
