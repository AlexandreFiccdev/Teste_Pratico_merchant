# Merchants API + Front-end

Sistema de cadastro e análise de Merchants (estabelecimentos comerciais), com API em Django REST
Framework e um front-end em Django (templates server-side) que consome essa API.

## Arquitetura

O projeto é dividido em dois serviços independentes, cada um em seu próprio container Docker:

| Serviço    | Stack                          | Porta | Papel                                                        |
|------------|---------------------------------|-------|---------------------------------------------------------------|
| `api`      | Django + Django REST Framework | 8000  | Regras de negócio, persistência (SQLite) e endpoints REST     |
| `frontend` | Django (templates)             | 8080  | Telas web que consomem a API via HTTP (biblioteca `requests`) |

O front-end **não acessa o banco de dados diretamente** — toda leitura/escrita de merchants passa
pela API, via a variável de ambiente `API_BASE_URL` (dentro do Docker aponta para
`http://api:8000/api`).

```
teste_pratico/
├── config/            # settings/urls da API
├── Merchants/         # app Django da API (models, views, serializers, testes)
├── Dockerfile          # imagem da API
├── docker-compose.yml  # orquestra api + frontend
├── requirements.txt    # deps da API
└── frontend/
    ├── config/            # settings/urls do front-end
    ├── merchants_ui/      # app Django do front-end (views, forms, templates, static)
    ├── Dockerfile         # imagem do front-end
    └── requirements.txt   # deps do front-end (Django + requests)
```

## Regras de negócio

Um merchant tem: CNPJ, razão social, nome fantasia, e-mail, telefone, data de criação e status.

Status possíveis: `draft` → `pending_analysis` → `approved` / `rejected`; um `approved` pode virar
`blocked`.

- CNPJ, razão social e e-mail são obrigatórios no cadastro; CNPJ deve ser único e ter 14 caracteres.
- O CNPJ segue a nova regra alfanumérica da Receita Federal: os 12 primeiros caracteres podem ser
  dígitos ou letras maiúsculas, e os 2 dígitos verificadores finais são sempre numéricos (cálculo
  via módulo 11, usando o código ASCII de cada caractere). Para gerar CNPJs válidos nesse formato
  para testes, use o
  [Simulador Nacional de CNPJ Alfanumérico da Receita Federal](https://servicos.receitafederal.gov.br/servico/cnpj-alfa/simular).
- O status inicial é sempre `draft`.
- Dados cadastrais só podem ser alterados enquanto o merchant estiver em `draft`.
- Envio para análise: só a partir de `draft` → `pending_analysis`.
- Aprovação: só a partir de `pending_analysis` → `approved`.
- Rejeição: só a partir de `pending_analysis` → `rejected`, motivo obrigatório.
- Bloqueio: só a partir de `approved` → `blocked`, motivo obrigatório.
- Cada uma dessas transições registra um evento na timeline do merchant.

## Como rodar (Docker)

Pré-requisito: Docker e Docker Compose instalados.

```bash
cd teste_pratico
docker compose up -d --build
```

Isso builda as duas imagens e sobe os containers. As migrations **não** rodam automaticamente
(nem no build, nem no start do container) — isso é proposital, para que a imagem da API possa ser
usada em qualquer ambiente sem gerar alterações no banco sem intenção explícita. Antes do primeiro
uso, aplique as migrations manualmente:

```bash
docker compose exec api python manage.py migrate
```

(ou `docker compose run --rm api python manage.py migrate`, se o container `api` ainda não estiver
rodando). Depois de alguns segundos:

- Front-end: http://localhost:8080/
- API: http://localhost:8000/api/merchants/
- Documentação da API (Swagger UI): http://localhost:8000/api/docs/

Para acompanhar os logs:

```bash
docker logs -f merchants_api
docker logs -f merchants_frontend
```

Para parar os containers (mantendo os dados no volume):

```bash
docker compose down
```

Para parar e apagar também os dados persistidos (`api_db_data`):

```bash
docker compose down -v
```

### Usando o front-end

1. Acesse http://localhost:8080/ — lista de merchants, com filtro por status.
2. **+ Novo Merchant** — cadastra (CNPJ, razão social, e-mail obrigatórios).
3. Clique em no icone de **Visualizar** em um merchant para abrir o detalhe: dados cadastrais + linha do tempo de
   eventos.
4. Na tela de detalhe, os botões de ação aparecem de acordo com o status atual:
   - `draft`: **Editar dados cadastrais** e **Enviar para análise**.
   - `pending_analysis`: **Aprovar** ou **Rejeitar** (motivo obrigatório).
   - `approved`: **Bloquear** (motivo obrigatório).
   - `rejected` / `blocked`: sem ações, estado final.

## Como rodar sem Docker (opcional, para desenvolvimento)

Requer Python 3.12+ e dois ambientes virtuais separados (API e front-end são projetos Django
distintos).

**API:**
```bash
cd teste_pratico
python -m venv venv
./venv/Scripts/activate       # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

**Front-end** (em outro terminal):
```bash
cd teste_pratico/frontend
python -m venv venv
./venv/Scripts/activate       # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8080
```

Sem a variável `API_BASE_URL` definida, o front-end usa `http://localhost:8000/api` por padrão —
funciona direto se a API estiver rodando localmente na porta 8000.

## Rodando os testes automatizados da API

```bash
cd teste_pratico
python manage.py test Merchants
```

(ou, com o container em pé: `docker exec merchants_api python manage.py test Merchants`)

## Documentação da API (Swagger)

A API é documentada com [drf-spectacular](https://drf-spectacular.readthedocs.io/) (OpenAPI 3).
Com a API rodando, a documentação interativa fica disponível em:

- Swagger UI: http://localhost:8000/api/docs/
- Redoc: http://localhost:8000/api/redoc/
- Schema OpenAPI (JSON/YAML): http://localhost:8000/api/schema/

Códigos de retorno: `201`/`200` sucesso, `400` erro de validação, `404` não encontrado, `409`
violação de regra de negócio (ex.: transição de status inválida).
