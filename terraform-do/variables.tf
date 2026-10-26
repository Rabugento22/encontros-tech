variable "region" {
  description = "Região DigitalOcean onde o cluster será criado."
  type        = string
  default     = "nyc3"
}

variable "cluster_name" {
  description = "Nome do cluster DOKS (também usado como tag dos nodes)."
  type        = string
  default     = "encontros-tech"
}

variable "node_size" {
  description = "Tamanho do droplet do node. s-1vcpu-2gb (~US$ 12/mês) é o menor que comporta os 2 pods (Flask + Postgres) com folga."
  type        = string
  default     = "s-1vcpu-2gb"
}

variable "node_count" {
  description = "Quantidade de nodes. 1 node comporta os dois pods e minimiza o custo (sem alta disponibilidade)."
  type        = number
  default     = 1
}
