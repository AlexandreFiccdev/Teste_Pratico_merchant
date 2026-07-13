# Decisões Técnicas

Resumo breve das escolhas feitas neste desafio prático e o porquê.

## Arquitetura

O projeto é dividido em dois serviços independentes, cada um em seu próprio container Docker:

| Serviço    | Stack                          | Porta | Papel                                                        |
|------------|---------------------------------|-------|---------------------------------------------------------------|
| `api`      | Django + Django REST Framework | 8000  | Regras de negócio, persistência (SQLite) e endpoints REST     |
| `frontend` | Django (templates)             | 8080  | Telas web que consomem a API via HTTP (biblioteca `requests`) |

O front-end **não acessa o banco de dados diretamente** — toda leitura/escrita de merchants passa
pela API, via a variável de ambiente `API_BASE_URL` (dentro do Docker aponta para
`http://api:8000/api`).

## Organização dos arquivos

```
teste_pratico/
├── config/            # settings/urls da API
├── Merchants/         # app Django da API (models, views, serializers, exceptions, validators)
│   └── tests/         # testes automatizados, um arquivo por responsabilidade
├── Dockerfile          # imagem da API
├── docker-compose.yml  # orquestra api + frontend
├── requirements.txt    # deps da API
└── frontend/
    ├── config/            # settings/urls do front-end
    ├── merchants_ui       # app Django do front-end (views, forms, services.py, templates) 
    ├── Dockerfile         # imagem do front-end
    └── requirements.txt   # deps do front-end (Django + requests)
```

Dentro de `Merchants/`, a separação segue o padrão DRF: `models.py` (dados + `MerchantStatus`
como `TextChoices`), `serializers.py` (validação/formatação, com um `MerchantFieldsMixin`
compartilhado entre list/detail para não duplicar mensagens de erro), `views.py`
(`ModelViewSet` + `@action` para as transições de status), `exceptions.py`
(`BusinessRuleError`, mapeada para HTTP 409), `validators/` (validação de CNPJ isolada por
ser regra de domínio reutilizável) e `tests/` (testes automatizados, ver seção
[Testes](#testes)).

No front, `services.py` concentra **toda** a comunicação HTTP com a API — as views nunca
chamam `requests` diretamente. Isso mantém as views finas (roteamento + tratamento de
mensagens) e torna o client HTTP fácil de testar/trocar isoladamente.

## Comunicação API ↔ Front

O front fala com a API só por HTTP/JSON, via `API_BASE_URL` (env var; aponta para
`http://api:8000/api` no Docker Compose e usa `http://localhost:8000/api` como default fora
dele). `services.py` é um wrapper fino sobre `requests`:

- Erros de rede/conexão viram `ApiUnavailableError` (tratada nas views como "API fora do
  ar").
- Erros HTTP (400/404/409) chegam como `HTTPError` do `requests` e o payload de erro do DRF
  é convertido de volta em erros de formulário Django (`_apply_api_errors_to_form`) ou em
  mensagens (`messages.error`), reaproveitando as mesmas mensagens de validação que a API já
  gera.
- Não há autenticação entre os dois serviços (`AllowAny` na API) — deliberado para o escopo
  do teste; em produção essa comunicação exigiria autenticação de serviço (token, mTLS etc).

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

## Testes

Testes automatizados da API (`Merchants/tests/`), organizados em um arquivo por
responsabilidade, com um `factories.py` compartilhado para o helper `merchant_payload`. O
front não tem testes automatizados dado o escopo do teste prático (é uma camada fina sobre a
API, já validada).

| Arquivo                       | Qtd. testes | O que testa |
|--------------------------------|:-----------:|-------------|
| `test_create.py`               | 14          | Criação de merchant (`POST /merchants/`): dados válidos, campos obrigatórios (cnpj, razão social, email), unicidade de CNPJ, validação de dígitos verificadores, formato alfanumérico (novo padrão CNPJ), case-insensitivity, normalização de máscara no cadastro (com/sem máscara → mesmo valor, e detecção de duplicata entre as duas formas), e que o cliente não pode forçar um status inicial diferente de `draft`. |
| `test_list.py`                 | 4           | Listagem e busca por ID (`GET /merchants/` e `GET /merchants/{id}/`): retrieve de um merchant existente (incluindo timeline de eventos), 404 para ID inexistente, listagem geral e listagem filtrada por status. |
| `test_update.py`               | 7           | Atualização de dados cadastrais (`PATCH /merchants/{id}/`): permitida em `draft`, bloqueada fora de `draft` (409), CNPJ duplicado/inválido/vazio rejeitados, manter o mesmo CNPJ ao atualizar outros campos é permitido, e validação de e-mail inválido. |
| `test_status_transitions.py`   | 11          | Máquina de estados (`submit-for-analysis`, `approve`, `reject`, `block`): cada transição válida muda o status e gera um `MerchantEvent`; cada transição fora do estado esperado retorna 409; `reject`/`block` exigem motivo (400 sem `reason`); e um teste de ponta a ponta conferindo a timeline completa em ordem. |

Total: 36 testes.

## Docker

Dois `Dockerfile`s + `docker-compose.yml` orquestrando os dois serviços, cada um com seu
próprio ambiente virtual/dependências (a API não depende de `requests`, o front não depende
de DRF). Volume nomeado para persistir o SQLite da API entre restarts dos containers.
