def merchant_payload(**overrides):
    payload = {
        "cnpj": "11222333000181",
        "razao_social": "Comercio Exemplo LTDA",
        "nome_fantasia": "Exemplo",
        "email": "contato@exemplo.com",
        "telefone": "11999998888",
    }
    payload.update(overrides)
    return payload
