#!/usr/bin/env python3
"""Popula a aplicação Encontros Tech com eventos de exemplo via API HTTP.

Os dados seguem o contrato de api-requests.http. O script é idempotente:
antes de criar, consulta a API (GET /api/events/?search=<título>) e só cria
o evento se nenhum resultado tiver exatamente o mesmo título.

Uso:
    python scripts/seed.py
    python scripts/seed.py --base-url http://localhost:8080

Códigos de saída: 0 sucesso, 1 erro da API/eventos não criados, 2 sem conexão.
"""
import argparse
import json
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE_URL = "http://localhost:8000"
EVENTS_PATH = "/api/events/"
TIMEOUT = 10
PAGE_SIZE = 100

SEED_EVENTS = [
    {
        "title": "Workshop: Introdução ao FastAPI",
        "description": "Aprenda a criar APIs REST modernas com FastAPI, incluindo documentação automática, validação de dados e deploy em produção.",
        "date": "2024-02-15T19:00:00",
        "location": "Centro de Convenções - São Paulo, SP",
        "technologies": ["Python", "FastAPI", "REST API", "Swagger"],
    },
    {
        "title": "Meetup React: Performance com Next.js 14",
        "description": "Discussão sobre otimização de performance em aplicações React usando as novas funcionalidades do Next.js 14.",
        "date": "2024-02-20T18:30:00",
        "location": "Hub de Inovação - Rio de Janeiro, RJ",
        "technologies": ["JavaScript", "React", "Next.js", "Frontend"],
    },
    {
        "title": "DevOps Conference 2024: Kubernetes na Prática",
        "description": "Evento focado em práticas DevOps modernas, com palestras sobre Kubernetes, CI/CD, monitoramento e observabilidade.",
        "date": "2024-03-05T09:00:00",
        "location": "Expo Center Norte - São Paulo, SP",
        "technologies": ["Kubernetes", "Docker", "CI/CD", "DevOps", "Prometheus", "Grafana"],
    },
    {
        "title": "Hackathon Mobile: Apps para Sustentabilidade",
        "description": "48 horas de desenvolvimento intensivo para criar aplicativos móveis que promovam sustentabilidade e consciência ambiental.",
        "date": "2024-02-25T08:00:00",
        "location": "Campus Universitário - Belo Horizonte, MG",
        "technologies": ["React Native", "Flutter", "Mobile", "Sustainability"],
    },
    {
        "title": "IA na Prática: Machine Learning com Python",
        "description": "Como implementar soluções de Machine Learning em produção usando Python, scikit-learn e TensorFlow.",
        "date": "2024-03-10T14:00:00",
        "location": "Auditório Tech Hub - Brasília, DF",
        "technologies": ["Python", "Machine Learning", "TensorFlow", "Scikit-learn", "AI"],
    },
    {
        "title": "AWS na Prática: Serverless com Lambda",
        "description": "Workshop hands-on sobre desenvolvimento serverless na AWS usando Lambda, API Gateway e DynamoDB.",
        "date": "2024-03-15T10:00:00",
        "location": "Centro de Treinamento - Porto Alegre, RS",
        "technologies": ["AWS", "Lambda", "Serverless", "DynamoDB", "Cloud"],
    },
    {
        "title": "PostgreSQL Avançado: Otimização e Performance",
        "description": "Técnicas avançadas de otimização em PostgreSQL, incluindo índices, particionamento e análise de performance.",
        "date": "2024-02-28T19:30:00",
        "location": "Coworking Space - Florianópolis, SC",
        "technologies": ["PostgreSQL", "Database", "SQL", "Performance"],
    },
    {
        "title": "Cybersecurity Summit: Proteção de APIs",
        "description": "Estratégias para proteger APIs REST contra ataques comuns, incluindo autenticação, autorização e monitoramento.",
        "date": "2024-03-20T13:00:00",
        "location": "Centro Empresarial - Curitiba, PR",
        "technologies": ["Security", "API Security", "JWT", "OAuth", "Cybersecurity"],
    },
    {
        "title": "Modern Frontend: Vue.js 3 + TypeScript",
        "description": "Desenvolvimento de aplicações frontend modernas com Vue.js 3, Composition API e TypeScript.",
        "date": "2024-04-05T15:00:00",
        "location": "Innovation Lab - Salvador, BA",
        "technologies": ["Vue.js", "TypeScript", "Frontend", "JavaScript"],
    },
    {
        "title": "Blockchain & Web3: Desenvolvimento de DApps",
        "description": "Introdução ao desenvolvimento de aplicações descentralizadas (DApps) usando Solidity e frameworks Web3.",
        "date": "2024-04-10T11:00:00",
        "location": "Tech Park - Recife, PE",
        "technologies": ["Blockchain", "Solidity", "Web3", "DApps", "Ethereum"],
    },
]


class ApiConnectionError(Exception):
    """Não foi possível alcançar a API (recusada, timeout, DNS...)."""


class ApiResponseError(Exception):
    """A API respondeu, mas com erro HTTP ou corpo inesperado."""


def request_json(method, url, payload=None):
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()[:200]
        raise ApiResponseError(f"{method} {url} -> HTTP {exc.code} {exc.reason}: {detail}") from exc
    except (urllib.error.URLError, socket.timeout, ConnectionError) as exc:
        reason = getattr(exc, "reason", exc)
        raise ApiConnectionError(f"{reason}") from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise ApiResponseError(f"{method} {url} -> resposta não é JSON válido") from exc


def title_exists(base_url, title):
    """True se a API já tem um evento com exatamente este título.

    O parâmetro `search` da API é um ILIKE por trecho (título, descrição e
    local), então ele só restringe os candidatos; a igualdade é conferida aqui.
    """
    skip = 0
    while True:
        query = urllib.parse.urlencode({"search": title, "skip": skip, "limit": PAGE_SIZE})
        page = request_json("GET", f"{base_url}{EVENTS_PATH}?{query}")
        if not isinstance(page, list):
            raise ApiResponseError("GET /api/events/ não retornou uma lista")
        if any(event.get("title") == title for event in page):
            return True
        if len(page) < PAGE_SIZE:
            return False
        skip += PAGE_SIZE


def seed(base_url):
    created = existing = 0
    failed = []
    for event in SEED_EVENTS:
        title = event["title"]
        if title_exists(base_url, title):
            existing += 1
            print(f"  = já existe: {title}")
            continue
        try:
            request_json("POST", f"{base_url}{EVENTS_PATH}", event)
        except ApiResponseError as exc:
            failed.append(title)
            print(f"  ! falhou:    {title} ({exc})", file=sys.stderr)
            continue
        created += 1
        print(f"  + criado:    {title}")
    return created, existing, failed


def main(argv=None):
    parser = argparse.ArgumentParser(description="Popula a API Encontros Tech com eventos de exemplo.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL,
                        help=f"URL base da aplicação (default: {DEFAULT_BASE_URL})")
    args = parser.parse_args(argv)
    base_url = args.base_url.rstrip("/")

    print(f"Populando eventos em {base_url}")
    try:
        created, existing, failed = seed(base_url)
    except ApiConnectionError as exc:
        print(f"\nErro: não foi possível conectar à API em {base_url} ({exc}).\n"
              f"Verifique se a aplicação está no ar e se --base-url está correto.", file=sys.stderr)
        return 2
    except ApiResponseError as exc:
        print(f"\nErro: resposta inesperada da API: {exc}", file=sys.stderr)
        return 1

    print(f"\nResumo: {created} criado(s), {existing} já existia(m)"
          + (f", {len(failed)} falhou(aram)" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
