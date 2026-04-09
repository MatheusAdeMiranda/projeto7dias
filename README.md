# uptime-tracker

API RESTful para monitoramento de servicos/sites.

## Objetivo

Construir um projeto de estudo orientado por entregas pequenas para praticar:

- Linux e WSL
- conceitos de sistema operacional
- portas e DNS
- Docker Compose
- API RESTful
- Git com boas praticas
- paralelismo com worker e fila

## Escopo do MVP

O primeiro recorte do projeto deve ser pequeno e util:

- cadastrar servicos
- listar servicos
- disparar checagens
- registrar historico basico das checagens

## Stack

- FastAPI na API
- PostgreSQL para persistencia
- Redis para fila e coordenacao
- worker separado
- Docker Compose para orquestracao local

## Estado atual

Dia 2 iniciado e com arquitetura minima executavel:

- `api` sobe com FastAPI e expone `/` e `/health`
- `postgres` e `redis` sobem com healthchecks proprios
- `worker` valida conectividade com `postgres` e `redis` e grava heartbeat
- `docker-compose.yml` publica as portas do host e conecta tudo pela rede interna padrao

## Como subir

O arquivo versionado `.env.example` e um template. O arquivo que o Docker Compose usa de verdade para interpolar variaveis e popular os containers e `.env`.

```bash
cp .env.example .env
docker compose config
docker compose up --build -d
```

No PowerShell, o equivalente e:

```powershell
Copy-Item .env.example .env
docker compose config
docker compose up --build -d
```

Depois disso:

- API: `http://localhost:8000`
- Healthcheck: `http://localhost:8000/health`
- Docs do FastAPI: `http://localhost:8000/docs`

## Como validar o Dia 2

Use estes comandos para fechar a verificacao objetiva da infraestrutura:

```bash
docker compose ps
docker compose logs --tail=50 api
docker compose logs --tail=50 worker
docker compose exec -T api sh -lc "pwd && ls -la"
docker compose exec -T api python -c "import socket; print('postgres ->', socket.gethostbyname('postgres')); print('redis ->', socket.gethostbyname('redis'))"
```

Do host, valide a porta publicada da API:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health" | ConvertTo-Json -Depth 6
```

Para fixar o conceito de `localhost` dentro do container:

```bash
docker compose exec -T api python -c "import socket; import urllib.request; print('api localhost:8000 ->', urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status); s=socket.socket(); s.settimeout(1); code=s.connect_ex(('127.0.0.1', 5432)); s.close(); print('api localhost:5432 connect_ex ->', code)"
```

Interpretacao esperada:

- `localhost:8000` dentro da API responde porque aponta para o proprio container da API
- `localhost:5432` dentro da API falha porque nao aponta para o Postgres
- `postgres` e `redis` resolvem por DNS interno do Docker Compose
- `localhost:8000` no host funciona porque a porta `8000` foi publicada pelo Compose
- se `postgres` ou `redis` cairem, o worker deixa de renovar heartbeat e o healthcheck dele deve ficar `unhealthy`

## O que praticar no Dia 2

- `localhost` no host aponta para sua maquina
- `localhost` dentro do container aponta para o proprio container
- a API fala com `postgres:5432` e `redis:6379` porque esses sao nomes de servico que viram DNS interno no Compose
- porta publicada existe para acesso de fora do container

## Estrutura atual

```text
uptime-tracker/
  README.md
  CLAUDE.md
  .gitignore
  .env.example
  docker-compose.yml
  api/
    Dockerfile
    requirements.txt
    app/
      main.py
    tests/
  worker/
    Dockerfile
    requirements.txt
    app/
      main.py
    tests/
```

## Proximo passo

Partir para o Dia 3 e desenhar o primeiro endpoint util da API com o runtime local ja confiavel.
