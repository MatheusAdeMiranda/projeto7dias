# uptime-tracker

API RESTful de monitoramento de servicos e sites construida em 7 dias como projeto de estudo orientado por entregas pequenas.

**Stack:** FastAPI · PostgreSQL · Redis · RQ worker · Docker Compose · Alembic · pytest

---

## O que faz

- Cadastra servicos a monitorar (nome, URL, status esperado, timeout)
- Dispara checagens HTTP assincronas via fila Redis
- Worker consome a fila, faz o request e grava o resultado no banco
- Expoe historico de checagens por servico
- Endpoint `/health` proba conectividade TCP com postgres e redis

## Endpoints

| Metodo | Rota | Descricao |
|--------|------|-----------|
| `GET` | `/health` | Status da API e dependencias |
| `POST` | `/services` | Cadastra servico |
| `GET` | `/services` | Lista servicos |
| `GET` | `/services/{id}` | Detalhe do servico |
| `POST` | `/services/{id}/checks` | Dispara checagem assincrona (202) |
| `GET` | `/services/{id}/checks` | Historico de checagens |

## Arquitetura

```
host
 └── Docker Compose
      ├── api        :8000   FastAPI + Alembic
      ├── postgres   :5432   persistencia
      ├── redis      :6379   fila de jobs
      └── worker             RQ worker
```

A API recebe o pedido de checagem, enfileira no Redis e retorna `202 Accepted`.
O worker consome o job, faz o request HTTP com `httpx`, e grava o `CheckResult` no Postgres.
A API le o resultado via `GET /services/{id}/checks`.

## Como rodar

Prerequisitos: Docker Desktop com WSL2 habilitado.

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

Validar:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

Criar um servico e disparar uma checagem:

```bash
curl -s -X POST http://localhost:8000/services \
  -H "Content-Type: application/json" \
  -d '{"name": "Example", "url": "https://example.com"}' | python -m json.tool

curl -s -X POST http://localhost:8000/services/1/checks

# aguardar o worker processar (~1s) e consultar o resultado
curl -s http://localhost:8000/services/1/checks | python -m json.tool
```

## Testes

```bash
docker compose exec api python -m pytest -q
```

Os testes usam SQLite isolado com schema aplicado via Alembic.
Nenhum teste depende de Docker em execucao.

## Estrutura

```
uptime-tracker/
  docker-compose.yml
  .env.example
  pyproject.toml          # ruff
  CLAUDE.md               # documentacao viva da arquitetura
  api/
    Dockerfile
    requirements.txt
    alembic.ini
    alembic/versions/     # migrations
    app/
      main.py             # rotas, handler de excecao
      db.py               # engine e sessao SQLAlchemy
      models.py           # ServiceModel, CheckResultModel
      schemas.py          # contratos Pydantic
      connectivity.py     # probe TCP para o /health
    tests/
      conftest.py
      test_services.py
      test_checks.py
      test_connectivity.py
      test_error_handling.py
  worker/
    Dockerfile
    requirements.txt
    app/
      main.py             # RQ Worker + heartbeat
      jobs.py             # run_check: HTTP check + persistencia
      db.py               # session factory para o worker
      models.py           # modelos SQLAlchemy (espelho da api)
```

## Decisoes tecnicas

- **Worker separado da API** para praticar fila e processamento assincrono sem acoplar ao ciclo de request/response
- **SQLite nos testes** com schema via Alembic mantem velocidade sem descolar do contrato do banco real
- **`pool_pre_ping`** evita conexoes mortas apos ociosidade
- **Handler global de excecao** garante que erros nao tratados retornam `{"detail": "internal server error"}` sem vazar stack trace
- **Heartbeat file** como healthcheck do worker — o RQ Worker bloqueia em `work()` e nao expoe porta HTTP

## O que este projeto pratica

- Linux/WSL, filesystem, processos e variaveis de ambiente
- Docker Compose: rede bridge, DNS interno, porta publicada, healthcheck, depends_on
- REST: recurso, verbo HTTP, status code, validacao de payload
- Banco: SQLAlchemy, Alembic, migrations, sessao, FK com CASCADE
- Paralelismo: fila, worker, I/O-bound, retry como proximo passo
- Git: branch por tarefa, commits pequenos, historico legivel
- Qualidade: ruff lint/format, pytest, CI no GitHub Actions

## Proximas evolucoes

1. **Retry com backoff** — `Retry(max=3)` no RQ, jobs que falham hoje sao perdidos
2. **Status atual em `GET /services/{id}`** — incluir o ultimo `CheckResult` na resposta
3. **Autenticacao por API key** — header `X-API-Key` para qualquer deploy publico
