# Encontros Tech

Aplicação web para cadastro e consulta de eventos de tecnologia.

> **Convenção deste documento:** cada afirmação tem origem em um arquivo do repositório
> (indicado entre parênteses). O que não pôde ser confirmado a partir do repositório está
> marcado como **A confirmar**.

## Sumário

1. [Visão geral](#visão-geral)
2. [Stack](#stack)
3. [Pré-requisitos](#pré-requisitos)
4. [Como rodar local](#como-rodar-local)
5. [Testes e dados de exemplo](#testes-e-dados-de-exemplo)
6. [Provisionar a infraestrutura com Terraform](#provisionar-a-infraestrutura-com-terraform)
7. [Deploy no cluster Kubernetes](#deploy-no-cluster-kubernetes)
8. [Endpoints de saúde](#endpoints-de-saúde)
9. [Variáveis de ambiente](#variáveis-de-ambiente)
10. [Limitações e pontos a confirmar](#limitações-e-pontos-a-confirmar)

## Visão geral

O Encontros Tech permite listar, buscar, criar e editar eventos de tecnologia, por páginas web
(`src/routers/page_router.py`, `src/templates/`) e por uma API HTTP/JSON (`src/routers/api_router.py`).

- Cada evento tem `title`, `description`, `date`, `location` e `technologies`
  (`src/schemas/event.py`).
- A edição é feita por um `edit_token` (UUID) gerado na criação do evento
  (`src/models/event.py`, rotas `/events/edit/<edit_token>` e `/api/events/by-token/<edit_token>`).
- A aplicação expõe métricas Prometheus em `/metrics` (`src/main.py`, `prometheus-flask-exporter`).

### Estrutura do repositório

```
.
├── docker-compose.yml        # app + PostgreSQL para rodar local
├── pytest.ini
├── api-requests.http         # contrato/exemplos das chamadas à API
├── scripts/seed.py           # popula a aplicação via HTTP
├── src/                      # aplicação Flask (Dockerfile, requirements.txt)
│   ├── core/                 # settings, database, logging
│   ├── routers/              # camada HTTP (api, pages, health)
│   ├── services/             # regras de negócio
│   ├── models/  schemas/     # SQLAlchemy e pydantic
│   ├── templates/  static/
│   └── tests/
├── k8s/
│   ├── encontros-tech.yaml   # todos os manifests em um único arquivo
│   └── kind/kind-config.yaml # configuração do cluster kind
└── terraform/                # cluster EKS na AWS
```

## Stack

| Componente | Versão declarada | Origem |
|---|---|---|
| Python | 3.13 (`python:3.13-slim`) | `src/Dockerfile` |
| Flask | 3.0.0 | `src/requirements.txt` |
| gunicorn | 21.2.0 | `src/requirements.txt` |
| SQLAlchemy | 2.0.43 | `src/requirements.txt` |
| psycopg2-binary | 2.9.10 | `src/requirements.txt` |
| pydantic / pydantic-settings | 2.11.7 / 2.10.1 | `src/requirements.txt` |
| Jinja2 / Werkzeug | 3.1.6 / 3.0.1 | `src/requirements.txt` |
| prometheus-flask-exporter / prometheus-client | 0.23.0 / 0.21.1 | `src/requirements.txt` |
| pytest | 8.3.4 | `src/requirements.txt` |
| PostgreSQL | 16 (`postgres:16-alpine`) | `docker-compose.yml`, `k8s/encontros-tech.yaml` |
| Terraform | `>= 1.5.0` | `terraform/providers.tf` |
| Provider AWS (Terraform) | `~> 5.0` | `terraform/providers.tf` |
| Kubernetes (EKS) | `1.36` (default da variável) | `terraform/variables.tf` |

Arquitetura em camadas: **router → service → model**, com `core/database.py` como único ponto de
configuração da conexão com o PostgreSQL (`src/core/database.py`).

## Pré-requisitos

| Para | Preciso de | Versão |
|---|---|---|
| Rodar local | Docker e Docker Compose | **A confirmar** (não declarada) |
| Testes e seed | Python 3.13 (o seed usa só a biblioteca padrão) | 3.13 (`src/Dockerfile`) |
| Cluster local | kind e kubectl | **A confirmar** (não declarada) |
| Terraform/AWS | Terraform `>= 1.5.0` (`terraform/providers.tf`), AWS CLI (usado em `kubeconfig_command`, `terraform/outputs.tf`) e credenciais AWS | AWS CLI: **A confirmar**; credenciais/permissões: **A confirmar** |

## Como rodar local

### Com Docker Compose

O `docker-compose.yml` define dois serviços: `db` (PostgreSQL 16, com healthcheck e volume
`pgdata`) e `app` (build de `./src` com o `src/Dockerfile`, porta `8000:8000`, só inicia depois
que o `db` estiver saudável).

```bash
# na raiz do repositório
docker compose up -d --build
```

Acesse:

- Aplicação: <http://localhost:8000>
- Saúde: <http://localhost:8000/health> e <http://localhost:8000/ready>

Parar:

```bash
docker compose down        # mantém os dados (volume pgdata)
docker compose down -v     # remove também os dados do banco
```

### Sem Docker

```bash
pip install -r src/requirements.txt
cd src && python main.py   # escuta em HOST:PORT (default 0.0.0.0:8000)
```

Requer um PostgreSQL acessível em `DATABASE_URL`; o default é
`postgresql://encontros_tech:encontros_tech@localhost:5432/encontros_tech`
(`src/core/settings.py`). Como provisionar esse banco localmente sem o compose: **A confirmar**
(o compose não publica a porta 5432 do `db`).

As variáveis podem vir de um arquivo `.env` (carregado por `load_dotenv()` em
`src/core/settings.py`); use `.env.exemple` (raiz) ou `src/.env.example` como modelo.

## Testes e dados de exemplo

### Testes

```bash
cd src
pytest
```

Execute a partir de `src/`: os testes importam módulos como `services` e `routers`, relativos a
`src/` (`src/tests/**`). Os testes são unitários, usam `MagicMock` e **não** precisam de banco.

### Popular com dados de exemplo

`scripts/seed.py` cria 10 eventos de exemplo **apenas por chamadas HTTP** à API
(`POST /api/events/`), sem acessar o banco.

```bash
python3 scripts/seed.py                                   # default: http://localhost:8000
python3 scripts/seed.py --base-url http://localhost:8080  # ex.: cluster kind
```

- **Idempotente**: antes de criar, consulta `GET /api/events/?search=<título>` e só cria se não
  houver evento com exatamente o mesmo título; rodar duas vezes não duplica.
- Ao final imprime quantos eventos foram criados e quantos já existiam.
- Códigos de saída: `0` sucesso, `1` erro da API/eventos não criados, `2` sem conexão com a API.

## Provisionar a infraestrutura com Terraform

A pasta `terraform/` cria um cluster **EKS** gerenciado na AWS.

| Recurso | Detalhe (`terraform/main.tf`) |
|---|---|
| VPC | CIDR `10.0.0.0/16` (variável `vpc_cidr`), DNS habilitado |
| Subnets | 2 públicas e 2 privadas, em 2 zonas de disponibilidade |
| Saída para a internet | 1 Internet Gateway e **1 NAT Gateway** (único) com route tables |
| IAM | role do cluster e role dos nodes, com as policies gerenciadas da AWS |
| Cluster EKS | endpoint público e privado; criador do cluster recebe admin (`access_config`) |
| Node group | gerenciado, em subnets privadas, `ON_DEMAND`, AMI `AL2023_x86_64_STANDARD` |

### Variáveis (`terraform/variables.tf`)

| Variável | Default | Descrição |
|---|---|---|
| `aws_region` | `us-east-1` | região AWS |
| `cluster_name` | `encontros-tech` | nome do cluster e prefixo dos recursos |
| `cluster_version` | `1.36` | versão do Kubernetes (formato `1.NN`, validado) |
| `cluster_creator_admin_permissions` | `true` | admin no cluster para quem executa o apply; alterar depois da criação força recriar o cluster |
| `vpc_cidr` | `10.0.0.0/16` | CIDR da VPC |
| `node_instance_type` | `t3.medium` | tipo de instância dos nodes |
| `node_desired_size` / `node_min_size` / `node_max_size` | `2` / `2` / `3` | tamanho do node group |
| `node_disk_size` | `20` | disco (GiB) por node |

### Comandos

```bash
cd terraform
terraform init
terraform plan                      # revise antes de aplicar
terraform apply
$(terraform output -raw kubeconfig_command)   # gera o kubeconfig
kubectl get nodes
terraform destroy                   # ao terminar
```

Outputs disponíveis (`terraform/outputs.tf`): `cluster_name`, `cluster_endpoint`, `region`,
`vpc_id`, `kubeconfig_command`.

Observações:

- O estado é **local** (não há `backend` em `terraform/providers.tf`); `*.tfstate` e `*.tfvars`
  são ignorados pelo `terraform/.gitignore`. O `.terraform.lock.hcl` é versionado.
- O Terraform **não** implanta a aplicação; o deploy é feito com os manifests de `k8s/`.
- Custos e permissões IAM necessárias para o `apply`: **A confirmar**.

## Deploy no cluster Kubernetes

Todos os manifests estão em um único arquivo: `k8s/encontros-tech.yaml`.

| # | Recurso | Nome | Função |
|---|---|---|---|
| 1 | ConfigMap | `encontros-tech-config` | variáveis não sensíveis: `APP_TITLE`, `DEBUG`, `SERVICE_NAME`, `SERVICE_VERSION` |
| 2 | Secret | `encontros-tech-secret` | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DATABASE_URL` |
| 3 | Service (headless) | `db` | DNS do PostgreSQL (porta 5432) |
| 4 | StatefulSet | `db` | `postgres:16-alpine`, PVC de 1Gi, probes `pg_isready` |
| 5 | Deployment | `encontros-tech` | app (porta 8000), initContainer `wait-for-db`, probes `/health` e `/ready` |
| 6 | Service (NodePort) | `encontros-tech` | porta 8000 → NodePort `30080` |

> O Secret contém credenciais de **desenvolvimento/teste** (as mesmas do compose), conforme o
> comentário no próprio manifest. Não versione credenciais reais.

### Ordem de aplicação

Basta aplicar o arquivo: o `kubectl apply` cria os recursos na ordem em que aparecem (1 → 6), e o
initContainer `wait-for-db` faz o app esperar o PostgreSQL aceitar conexões.

```bash
kubectl apply -f k8s/encontros-tech.yaml
kubectl rollout status statefulset/db
kubectl rollout status deployment/encontros-tech
kubectl get pods
```

### Cluster local com kind

O `k8s/kind/kind-config.yaml` mapeia a porta `8080` do host para o NodePort `30080`.

```bash
kind create cluster --name encontros-tech --config k8s/kind/kind-config.yaml
# a imagem é construída localmente pelo compose; carregue-a no cluster:
docker compose build
kind load docker-image rubensrsilva/encontros-tech-pos:latest --name encontros-tech
kubectl apply -f k8s/encontros-tech.yaml
```

Acesse <http://localhost:8080>. Para remover: `kind delete cluster --name encontros-tech`
(o nome `encontros-tech` é um exemplo, não é definido em arquivo do repositório).

### Em um cluster EKS

Gere o kubeconfig (seção Terraform) e aplique o mesmo manifest. Pontos **A confirmar**:

- a imagem `rubensrsilva/encontros-tech-pos:latest` estar publicada no registro;
- como expor a aplicação externamente (o Service é `NodePort`; não há LoadBalancer/Ingress);
- StorageClass/driver de volumes para o PVC do PostgreSQL.

## Endpoints de saúde

| Endpoint | Tipo | O que faz | Respostas |
|---|---|---|---|
| `GET /health` | **liveness** | indica apenas que o processo está vivo; **não** consulta banco nem dependências | `200` `{"status":"ok"}` |
| `GET /ready` | **readiness** | executa `SELECT 1` no PostgreSQL com a conexão já configurada | `200` `{"status":"ready"}` ou `503` `{"status":"not ready","reason":"<erro>"}` |

Origem: `src/routers/health_router.py` e `src/services/health_service.py`.

**Liveness vs readiness:** a liveness diz ao Kubernetes *se deve reiniciar* o container; por isso
não depende do banco (uma queda do PostgreSQL não reinicia a app). A readiness diz *se o pod pode
receber tráfego*; quando o banco cai, o pod sai do Service sem ser reiniciado e volta sozinho
quando o banco retorna.

Probes configuradas no Deployment (`k8s/encontros-tech.yaml`):

| Probe | Path | initialDelay | period | timeout | failureThreshold |
|---|---|---|---|---|---|
| liveness | `/health` | 15s | 10s | 3s | 3 |
| readiness | `/ready` | 5s | 5s | 5s | 3 |

```bash
curl -i http://localhost:8000/health
curl -i http://localhost:8000/ready
```

## Variáveis de ambiente

Lidas pela aplicação em `src/core/settings.py`:

| Variável | Default | Descrição |
|---|---|---|
| `DATABASE_URL` | `postgresql://encontros_tech:encontros_tech@localhost:5432/encontros_tech` | URL de conexão com o PostgreSQL. **Sensível** (contém senha); no cluster vem do Secret |
| `APP_TITLE` | `Encontros Tech` | título da aplicação (lido em `settings`; sem outro uso no código) |
| `DEBUG` | `false` | modo debug; também define `LOG_LEVEL` padrão como `DEBUG` |
| `HOST` | `0.0.0.0` | host quando executado com `python main.py` |
| `PORT` | `8000` | porta quando executado com `python main.py` |
| `LOG_LEVEL` | `INFO` (ou `DEBUG` se `DEBUG=true`) | nível de log |
| `LOG_FORMAT` | `colored` | formato do log: `colored` ou `simple` |
| `SERVICE_NAME` | `encontros-tech` | nome do serviço nos logs |
| `SERVICE_VERSION` | `1.0.0` | versão do serviço (log e métrica `app_info`) |
| `PROMETHEUS_MULTIPROC_DIR` | `/tmp/prometheus_multiproc` | diretório criado para métricas Prometheus |

Usadas pelo container do PostgreSQL (`docker-compose.yml`, Secret em `k8s/encontros-tech.yaml`):

| Variável | Descrição |
|---|---|
| `POSTGRES_USER` | usuário do banco |
| `POSTGRES_PASSWORD` | senha do banco (**sensível**) |
| `POSTGRES_DB` | nome do banco |

Outras observações:

- `PROMETHEUS_PORT` aparece em `.env.exemple` e `src/.env.example`, mas **nenhum código a lê**.
- No `docker-compose.yml`, os valores são definidos diretamente (`environment:`), não vindos de `.env`.
- No cluster, as não sensíveis vêm do ConfigMap e as sensíveis do Secret (`envFrom` no Deployment).

## Limitações e pontos a confirmar

- **`technologies` não é persistido**: o serviço apenas devolve a lista no objeto, sem gravar no
  banco (comentário em `src/services/event_service.py`); a listagem retorna `technologies: []`.
- **`SECRET_KEY` fixa no código**, com `TODO: Move to settings` (`src/main.py`).
- **`api-requests.http`** cita `/docs` e `/redoc`, que não existem na aplicação Flask.
- **Logs de probes**: toda requisição é logada em INFO (`src/main.py`), incluindo `/health` e `/ready`.
- **Versões de Docker, Compose, kind, kubectl e AWS CLI**, permissões/custos AWS e a exposição
  externa no EKS: **A confirmar** (ver seções acima).
