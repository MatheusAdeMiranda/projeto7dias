# CLAUDE.md

## Objetivo
API RESTful para monitoramento de servicos/sites.

## Stack
- FastAPI
- PostgreSQL
- Redis
- worker
- Docker Compose

## Arquitetura
- api: recebe requests HTTP e expoe os endpoints REST
- postgres: persiste services e check_results
- redis: fila para jobs assincronos e cache simples se necessario
- worker: executa checagens assincronas e grava resultados

## Estado atual
- Dia 1 concluido com repositorio e documentacao viva
- Dia 2 concluido com arquitetura local executavel via Docker Compose
- Dia 3 concluido com desenho REST do recurso `Service`
- Dia 4 concluido com persistencia real para `Service` via SQLAlchemy e Alembic
- Dia 5 concluido com fila assincrona via RQ/Redis, worker executando jobs e modelo `CheckResult`
- Dia 6 concluido com lint (ruff), refactor de connectivity helpers e pipeline de CI no GitHub Actions
- API exposta com `/`, `/health`, `POST /services`, `GET /services`, `GET /services/{id}`, `POST /services/{id}/checks`, `GET /services/{id}/checks`
- Worker consome fila `checks`, faz request HTTP com httpx e grava resultado no Postgres
- Fluxo ponta a ponta validado em runtime: job enfileirado pela API, consumido pelo worker, resultado persistido e consultavel pela API
- `ruff check .` rodando limpo em toda a arvore (config em `pyproject.toml` na raiz)
- CI em `.github/workflows/ci.yml` roda lint + pytest em todo push e PR

## Portas
- api: 8000
- postgres: 5432
- redis: 6379

## Servicos previstos no compose
- api
- postgres
- redis
- worker

## Regras do projeto
- small releases
- TDD nas features principais
- refactoring continuo
- nada de over-engineering

## Fluxos principais
- criar servico
- listar servicos
- consultar servico por id
- disparar checagem
- consultar historico

## Recursos REST atuais
- `POST /services`
- `GET /services`
- `GET /services/{id}`
- `POST /services/{id}/checks` — enfileira checagem, retorna 202 Accepted
- `GET /services/{id}/checks` — lista historico de checagens ordenado por data desc

## Modelos
- `Service`
  - id
  - name
  - url
  - expected_status
  - timeout_seconds
  - active
- `CheckResult`
  - id
  - service_id (FK -> services.id, CASCADE)
  - status (ok | error | timeout)
  - response_time_ms (nullable)
  - http_status_code (nullable)
  - checked_at (timezone-aware)
  - error_message (nullable)

## Variaveis de ambiente
- APP_ENV
- API_HOST
- API_PORT
- DATABASE_URL
- REDIS_URL
- POSTGRES_DB
- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_PORT
- REDIS_PORT

## Decisoes
- o projeto sera construido em etapas pequenas e verificaveis
- a arquitetura inicial sera de 4 servicos no desenvolvimento local
- o worker sera separado da API para praticar fila e processamento assincrono
- as portas padrao serao mantidas no inicio para reduzir variaveis
- o Compose usara os nomes `postgres` e `redis` como DNS interno entre containers
- o arquivo `.env.example` e apenas template; o runtime local usa `.env`
- o healthcheck da API validara a conectividade TCP com postgres e redis
- o healthcheck do worker e baseado em heartbeat local renovado por uma thread daemon enquanto o processo do worker estiver vivo (independente da disponibilidade de postgres/redis, ja que o RQ Worker bloqueia em `work()` e gerencia reconexao com o Redis internamente)
- no Dia 3, `Service` ficou em memoria para focar em recurso REST, contrato HTTP e validacao antes da persistencia real
- no Dia 4, `Service` passa a persistir em Postgres via SQLAlchemy e sessao sincrona simples
- a migration inicial sera gerenciada por Alembic a partir da versao `20260412_01`
- no ambiente local com Docker Compose, a API aplica `alembic upgrade head` antes de subir o servidor
- os testes da API usam SQLite isolado com override de dependencia, mas sobem o schema via Alembic para manter aderencia ao runtime real
- a estrutura do Alembic inclui `script.py.mako` para nao travar a proxima criacao de revision
- o primeiro recorte persistido cobre criacao, listagem e leitura por id, sem ainda introduzir `CheckResult`

## Modulos da API
- `app/main.py`: FastAPI app, rotas e dependencias
- `app/db.py`: engine e sessao do SQLAlchemy
- `app/models.py`: `ServiceModel`, `CheckResultModel`
- `app/schemas.py`: contratos Pydantic de entrada/saida
- `app/connectivity.py`: helpers TCP (`probe_tcp`, `resolve_host_port`) usados pelo `/health`

## Verificacoes atuais
- `docker compose ps` mostra `api`, `postgres`, `redis` e `worker` como `healthy`
- o host acessa a API por `http://localhost:8000/health`
- dentro do container `api`, `postgres` e `redis` resolvem por DNS interno do Compose
- dentro do container `api`, `127.0.0.1:5432` nao aponta para o Postgres, reforcando a diferenca entre localhost do container e servico remoto
- `docker compose exec api alembic -c alembic.ini upgrade head` aplica as duas migrations (services e check_results)
- `docker compose exec postgres psql -U postgres -d uptime -c "\dt"` mostra `services`, `check_results` e `alembic_version`
- `docker compose exec api python -m pytest -q` passa com 10 testes (services + checks)
- `POST /services/{id}/checks` retorna 202, enfileira job no Redis e o worker consome e persiste resultado

## Decisoes abertas
- se a estrutura de repositorio vai precisar de uma camada de repositorio/servico
- como comparar `http_status_code` com `expected_status` e atualizar status do servico
- se vale expor status atual do servico no `GET /services/{id}`

## Dividas tecnicas
- autenticar API
- rate limiting
- dashboard
- retry de jobs no worker (RQ suporta via `Retry(max=...)` mas nao foi habilitado no Dia 5)
- idempotencia: hoje `POST /services/{id}/checks` chamado duas vezes seguidas enfileira dois jobs e gera dois `CheckResult`. Sem chave de deduplicacao
- modelos `Service`/`CheckResult` duplicados entre `api/` e `worker/` por nao haver pacote compartilhado; mudancas no schema precisam ser replicadas em ambos
- conexao do worker com Postgres recriada por job (correto para o modelo de fork do RQ, mas custa overhead em volume alto)

## Observacoes de ambiente
- o repositorio foi iniciado no Windows para destravar o Dia 1
- a casa principal do projeto passa a ser /home/matheusmiranda/dev/uptime-tracker no Ubuntu do WSL
- a copia no Windows pode ser mantida apenas como apoio temporario, mas o desenvolvimento deve seguir no filesystem Linux
- o stack do Dia 2 pode ser validado com `cp .env.example .env`, `docker compose config` e `docker compose up --build`
