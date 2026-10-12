variable "aws_region" {
  description = "Região AWS onde o cluster será criado."
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "Nome do cluster EKS (também usado como prefixo dos recursos de rede e IAM)."
  type        = string
  default     = "encontros-tech"
}

variable "cluster_version" {
  description = "Versão do Kubernetes (minor, ex.: 1.36). Use uma versão em suporte padrão do EKS; versões antigas entram em suporte estendido, com cobrança extra por hora."
  type        = string
  default     = "1.36"

  validation {
    condition     = can(regex("^1\\.[0-9]+$", var.cluster_version))
    error_message = "cluster_version deve estar no formato 1.NN (ex.: 1.36)."
  }
}

variable "vpc_cidr" {
  description = "CIDR da VPC dedicada."
  type        = string
  default     = "10.0.0.0/16"
}

variable "node_instance_type" {
  description = "Tipo de instância EC2 dos nodes. A app (Flask + gunicorn, ~80 MiB) e o Postgres cabem folgadamente em t3.medium."
  type        = string
  default     = "t3.medium"
}

variable "node_desired_size" {
  description = "Quantidade desejada de nodes (2 = um por zona de disponibilidade)."
  type        = number
  default     = 2
}

variable "node_min_size" {
  description = "Quantidade mínima de nodes."
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Quantidade máxima de nodes."
  type        = number
  default     = 3
}

variable "node_disk_size" {
  description = "Tamanho do disco (GiB) de cada node."
  type        = number
  default     = 20
}
