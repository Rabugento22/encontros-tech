output "cluster_name" {
  description = "Nome do cluster DOKS."
  value       = digitalocean_kubernetes_cluster.this.name
}

output "cluster_endpoint" {
  description = "Endpoint da API do Kubernetes."
  value       = digitalocean_kubernetes_cluster.this.endpoint
}

output "kubeconfig_command" {
  description = "Comando para gerar/atualizar o kubeconfig e acessar o cluster com kubectl (requer doctl)."
  value       = "doctl kubernetes cluster kubeconfig save ${digitalocean_kubernetes_cluster.this.id}"
}
