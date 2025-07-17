def test_listar_arvores_vazio(client):
    # Assume DB vazio
    response = client.get('/arvores')
    assert response.status_code == 200
    assert response.get_json() == []

def test_cadastrar_arvore(client):
    nova_arvore = {
        "especie": "Ipê Amarelo",
        "latitude": "-22.1",
        "longitude": "-47.2",
        "endereco": "Rua das Árvores",
        "bairro": "Centro"
    }
    resp = client.post('/arvores', json=nova_arvore)
    assert resp.status_code == 201
    dados = resp.get_json()
    assert "id" in dados
    assert dados["message"] == "Árvore cadastrada!"
