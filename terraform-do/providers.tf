terraform {
  required_version = ">= 1.5.0"

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

# O token é lido da variável de ambiente DIGITALOCEAN_TOKEN (não fica no código).
provider "digitalocean" {}
