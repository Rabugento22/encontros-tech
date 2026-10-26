# ---------------------------------------------------------------------------
# Cluster DOKS enxuto: control plane gratuito (não-HA) + 1 node pequeno.
# Os 2 pods (app + Postgres) rodam no mesmo node; o custo fixo é só o droplet.
# ---------------------------------------------------------------------------

data "digitalocean_kubernetes_versions" "current" {}

resource "digitalocean_kubernetes_cluster" "this" {
  name          = var.cluster_name
  region        = var.region
  version       = data.digitalocean_kubernetes_versions.current.latest_version
  ha            = false # control plane HA custa extra
  auto_upgrade  = false
  surge_upgrade = false # evita criar node extra (e cobrança) durante upgrades

  node_pool {
    name       = "${var.cluster_name}-nodes"
    size       = var.node_size
    node_count = var.node_count
    auto_scale = false
    tags       = [var.cluster_name]
  }

  lifecycle {
    # A versão é escolhida na criação; não recria/atualiza o cluster quando sair uma nova.
    ignore_changes = [version]
  }
}
