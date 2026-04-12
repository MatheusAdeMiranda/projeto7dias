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
- Dia 4 iniciado com persistencia real para `Service`
- API inicial exposta com `/`, `/health`, `POST /services`, `GET /services` e `GET /services/{id}`
- worker inicial faz probes de conectividade e grava heartbeat para healthcheck
- Dia 2 validado em runtime com containers saudaveis e acesso confirmado pelo host
- Dia 3 validado com contrato HTTP inicial e testes da API
- Dia 4 validado com migration inicial, persistencia em Postgres e testes isolados da API

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

## Modelo inicial
- `Service`
  - id
  - name
  - url
  - expected_status
  - timeout_seconds
  - active

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
- WORKER_CHECK_INTERVAL

## Decisoes
- o projeto sera construido em etapas pequenas e verificaveis
- a arquitetura inicial sera de 4 servicos no desenvolvimento local
- o worker sera separado da API para praticar fila e processamento assincrono
- as portas padrao serao mantidas no inicio para reduzir variaveis
- o Compose usara os nomes `postgres` e `redis` como DNS interno entre containers
- o arquivo `.env.example` e apenas template; o runtime local usa `.env`
- o healthcheck da API validara a conectividade TCP com postgres e redis
- o healthcheck do worker sera baseado em heartbeat local renovado apenas quando postgres e redis estiverem acessiveis
- no Dia 3, `Service` ficou em memoria para focar em recurso REST, contrato HTTP e validacao antes da persistencia real
- no Dia 4, `Service` passa a persistir em Postgres via SQLAlchemy e sessao sincrona simples
- a migration inicial sera gerenciada por Alembic a partir da versao `20260412_01`
- no ambiente local com Docker Compose, a API aplica `alembic upgrade head` antes de subir o servidor
- os testes da API usam SQLite isolado com override de dependencia, mas sobem o schema via Alembic para manter aderencia ao runtime real
- a estrutura do Alembic inclui `script.py.mako` para nao travar a proxima criacao de revision
- o primeiro recorte persistido cobre criacao, listagem e leitura por id, sem ainda introduzir `CheckResult`

## Verificacoes atuais
- `docker compose ps` mostra `api`, `postgres`, `redis` e `worker` como `healthy`
- o host acessa a API por `http://localhost:8000/health`
- dentro do container `api`, `postgres` e `redis` resolvem por DNS interno do Compose
- dentro do container `api`, `127.0.0.1:5432` nao aponta para o Postgres, reforcando a diferenca entre localhost do container e servico remoto
- `docker compose exec api alembic -c alembic.ini upgrade head` aplica a migration inicial
- `docker compose exec postgres psql -U postgres -d uptime -c "\dt"` mostra `services` e `alembic_version`
- `docker compose exec api python -m pytest -q` passa com testes isolados de criacao, listagem e leitura usando Alembic no setup

## Decisoes abertas
- qual biblioteca de fila usar no worker
- qual ORM ou camada de acesso a dados usar
- como vamos modelar e persistir `CheckResult`
- se a estrutura de repositorio vai precisar de uma camada de repositorio/servico antes do Dia 5

## Dividas tecnicas
- autenticar API
- rate limiting
- dashboard

## Observacoes de ambiente
- o repositorio foi iniciado no Windows para destravar o Dia 1
- a casa principal do projeto passa a ser /home/matheusmiranda/dev/uptime-tracker no Ubuntu do WSL
- a copia no Windows pode ser mantida apenas como apoio temporario, mas o desenvolvimento deve seguir no filesystem Linux
- o stack do Dia 2 pode ser validado com `cp .env.example .env`, `docker compose config` e `docker compose up --build`
