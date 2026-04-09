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

Dia 1 em andamento:

- base do repositorio criada
- documentacao viva iniciada
- estrutura inicial de pastas preparada
- ambiente WSL2 validado e pronto para ser a casa principal do projeto

## Estrutura inicial

```text
uptime-tracker/
  README.md
  CLAUDE.md
  .gitignore
  .env.example
  api/
    app/
  worker/
    app/
```

## Proximo passo

Trabalhar a partir do Ubuntu no WSL em `~/dev/uptime-tracker` e fechar o checklist do Dia 1.
