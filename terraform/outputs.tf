output "cluster_name" {
  description = "Nome do cluster EKS."
  value       = aws_eks_cluster.this.name
}

output "cluster_endpoint" {
  description = "Endpoint da API do Kubernetes."
  value       = aws_eks_cluster.this.endpoint
}

output "region" {
  description = "Região AWS do cluster."
  value       = var.aws_region
}

output "vpc_id" {
  description = "ID da VPC dedicada."
  value       = aws_vpc.this.id
}

output "kubeconfig_command" {
  description = "Comando para gerar/atualizar o kubeconfig e acessar o cluster com kubectl."
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.this.name}"
}
