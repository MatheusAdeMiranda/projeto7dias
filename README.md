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

Dia 4 iniciado sobre a base estavel dos Dias 2 e 3:

- `api` sobe com FastAPI e expoe `/`, `/health`, `POST /services`, `GET /services` e `GET /services/{id}`
- `services` agora persiste no PostgreSQL usando SQLAlchemy
- a migration inicial e gerenciada com Alembic
- os testes da API usam SQLite isolado e sobem o schema via Alembic para manter velocidade sem descolar do runtime real
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
- ao subir a API no Compose, a migration mais recente e aplicada automaticamente no ambiente local

## Como validar o Dia 4

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

Para validar a migration inicial e o fluxo persistido do Dia 4:

```powershell
docker compose up -d --build
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/services" -ContentType "application/json" -Body '{"name":"OpenAI","url":"https://openai.com"}' | ConvertTo-Json -Depth 6
Invoke-RestMethod -Uri "http://localhost:8000/services" | ConvertTo-Json -Depth 6
Invoke-RestMethod -Uri "http://localhost:8000/services/1" | ConvertTo-Json -Depth 6
docker compose exec api python -m pytest -q
docker compose exec postgres psql -U postgres -d uptime -c "select * from services;"
```

Se quiser reaplicar manualmente por estudo ou debug:

```powershell
docker compose exec api alembic -c alembic.ini upgrade head
```

## O que praticar no Dia 2

- `localhost` no host aponta para sua maquina
- `localhost` dentro do container aponta para o proprio container
- a API fala com `postgres:5432` e `redis:6379` porque esses sao nomes de servico que viram DNS interno no Compose
- porta publicada existe para acesso de fora do container

## O que praticar no Dia 3

- modelagem de recurso REST antes de pensar em banco
- payload valido, payload invalido e status codes
- escolha do menor endpoint util
- diferenca entre prototipo em memoria e persistencia real

## O que praticar no Dia 4

- TDD como rede de seguranca antes da persistencia real
- diferenca entre teste isolado e runtime real
- sessao de banco, commit, refresh e leitura ordenada
- migration inicial como parte da evolucao do schema
- fixture de teste alinhada com o caminho real de migration

## Estrutura atual

```text
uptime-tracker/
  README.md
  CLAUDE.md
  .gitignore
  .env.example
  docker-compose.yml
  api/
    alembic.ini
    alembic/
      env.py
      script.py.mako
      versions/
    Dockerfile
    requirements.txt
    app/
      db.py
      main.py
      models.py
      schemas.py
    tests/
      conftest.py
  worker/
    Dockerfile
    requirements.txt
    app/
      main.py
    tests/
```

## Proximo passo

Partir para o Dia 5 e introduzir `CheckResult`, fila e worker de verdade, mantendo o mesmo nivel de TDD e small releases.
