terraform {
  backend "s3" {
    key          = "text-to-audio-polly/terraform.tfstate"
    region       = "eu-west-1"
    use_lockfile = true
    encrypt      = true
  }
}