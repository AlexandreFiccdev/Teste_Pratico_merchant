# Merchants API + Front-end

Sistema de cadastro e análise de Merchants (estabelecimentos comerciais), com API em Django REST
Framework e um front-end em Django (templates server-side) que consome essa API.

Para entender melhor como a regra de negócio, a arquitetura, os testes e outras decisões do
projeto foram pensados, veja [DECISOES_TECNICAS.md](DECISOES_TECNICAS.md).

## Obtendo o projeto

Escolha uma das opções abaixo para ter o código na sua máquina. Os passos seguintes deste README
assumem que você está com o terminal aberto dentro da pasta `teste_pratico/`.

**Opção 1 — clonando via Git:**

```bash
git clone https://github.com/AlexandreFiccdev/Teste_Pratico_merchant.git teste_pratico
cd teste_pratico
```

**Opção 2 — a partir de um arquivo `.zip`:**

A forma mais simples é extrair pelo Explorador de Arquivos do Windows: clique com o botão
direito no `.zip` → **Extrair Tudo...** → escolha o destino, e abra o terminal dentro da pasta
extraída (a que contém este `README.md`).

Se preferir via terminal:

```bash
# Windows — no PowerShell
Expand-Archive Teste_Pratico_merchant-main.zip -DestinationPath .
cd Teste_Pratico_merchant-main

# Linux/Mac
unzip Teste_Pratico_merchant-main.zip
cd Teste_Pratico_merchant-main
```

Os comandos das seções seguintes usam `teste_pratico/` como referência à raiz do projeto — se a
sua pasta tiver outro nome (como no exemplo acima), rode os comandos a partir dela mesma.

## Como rodar o programa (Recomendado)

Pré-requisito: Docker e Docker Compose instalados.

```bash
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
