# 🚀 Guia de Implementação - Fase 1

## 1️⃣ Atualizar Dependências

```bash
cd backend
pip install -r requirements.txt
```

## 2️⃣ Sincronizar Banco de Dados

Antes de rodar a migração, **faça um backup**:

```bash
pg_dump -U seu_usuario seu_banco > backup_antes.sql
```

Execute a migração:

```bash
# Diretamente pelo psql
psql -U seu_usuario -d seu_banco -f migrations/001_sync_ddl_with_models.sql

# OU via Python
# from database import engine
# with engine.connect() as conn:
#     with open('migrations/001_sync_ddl_with_models.sql') as f:
#         conn.execute(text(f.read()))
#     conn.commit()
```

## 3️⃣ Testar as Mudanças

### Teste 1: Context Manager
```bash
python
>>> from database import get_session, Requerente
>>> with get_session() as session:
...     requerentes = session.query(Requerente).all()
...     print(f"Total: {len(requerentes)}")
>>> # Sem erros? ✅
```

### Teste 2: Validação com Marshmallow
```bash
curl -X POST http://localhost:5000/api/requerency-requerente \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Jo",  # Nome muito curto
    "telefone": "123"
  }'

# Resposta esperada: Erro de validação (nome < 3 chars)
{
  "error": "Erro de validação",
  "details": {
    "nome": ["Shorter than minimum length 3."]
  }
}
```

### Teste 3: Campo Ativo do User
```bash
python
>>> from database import get_session, User
>>> with get_session() as session:
...     user = session.query(User).first()
...     print(f"Ativo é boolean? {isinstance(user.ativo, bool)}")
...     print(f"Valor: {user.ativo}")
>>> # Deve mostrar que é boolean ✅
```

## 4️⃣ Verificar Outras Rotas

A maioria das rotas já foi atualizada, mas se found problemas:

### Para adicionar validação a uma rota:

```python
# routes/minha_rota.py
from schemas import MeuSchema
from marshmallow import ValidationError

@minha_bp.route('/novo', methods=['POST'])
@login_required
def criar():
    schema = MeuSchema()
    try:
        dados = schema.load(request.get_json())
        
        with get_session() as session:
            novo = MeuModelo(**dados)
            session.add(novo)
        
        return jsonify({"message": "Criado!", "id": novo.id}), 201
    except ValidationError as e:
        return jsonify({"error": "Validação", "details": e.messages}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

## 5️⃣ Adicionar Mais Schemas

Se precisar adicionar validação a novos endpoints:

```python
# Em schemas.py - adicionar nova schema
from marshmallow import Schema, fields, validate

class MinhaSchema(Schema):
    campo1 = fields.String(required=True, validate=validate.Length(min=3))
    campo2 = fields.Email()
    campo3 = fields.Integer()
```

## 6️⃣ Tratamento de Erros

Agora você pode usar exceções tipadas:

```python
from errors import NotFoundError, ValidationError, ConflictError

@minha_bp.route('/<int:id>')
def obter(id):
    with get_session() as session:
        objeto = session.query(MeuModelo).get(id)
        if not objeto:
            raise NotFoundError("Objeto não encontrado")
        return jsonify(objeto.to_dict()), 200

@minha_bp.route('/', methods=['POST'])
def criar():
    dados = request.get_json()
    
    with get_session() as session:
        # Verificar duplicatas
        existe = session.query(MeuModelo).filter_by(email=dados.get('email')).first()
        if existe:
            raise ConflictError("Email já cadastrado")
        
        novo = MeuModelo(**dados)
        session.add(novo)
    
    return jsonify({"id": novo.id}), 201
```

## 7️⃣ Problemas Conhecidos

### Se encontrar erro ao executar migração:

```bash
# Erro: "table tarefas already exists"
# Solução: A tabela pode já existir no banco
# Verifique e remova:
# DROP TABLE IF EXISTS tarefas CASCADE;
# Depois execute novamente
```

### Se encontrar erro com tipo Boolean:

```bash
# Erro: "ativo não é boolean"
# Solução: Alguns registros têm string 'True'/'False'
# A migração cuida disso automaticamente
```

## 📊 Checklist Pós-Implementação

- [ ] `pip install -r requirements.txt` executado
- [ ] Migration SQL executada com sucesso
- [ ] Backup do banco feito antes da migração
- [ ] Teste 1: Context manager OK
- [ ] Teste 2: Validação Marshmallow OK
- [ ] Teste 3: Campo Boolean OK
- [ ] Testes manuais das rotas executados
- [ ] Documentação (IMPROVEMENTS.md) lida
- [ ] Nenhum erro em startup da app

## 🐛 Se Algo Deu Errado

1. **Restaurar backup**:
   ```bash
   psql -U seu_usuario seu_banco < backup_antes.sql
   ```

2. **Verificar logs**:
   ```bash
   # Flask logs
   # Verifique terminal onde flask está rodando
   ```

3. **Testar conexão**:
   ```python
   from database import get_session
   try:
       with get_session() as session:
           print("DB conectado ✅")
   except Exception as e:
       print(f"Erro: {e}")
   ```

## 📞 Próximas Melhorias

Quando terminar Fase 1, passar para Fase 2:

1. Criar Service Layer (requerimento_service.py, etc)
2. Extrair Serializers centralizados
3. Adicionar Logging estruturado
4. Setup de Cache Redis
5. Documentação Swagger/OpenAPI

Veja [IMPROVEMENTS.md](IMPROVEMENTS.md) para mais detalhes.

---

Generated on: 2026-03-03
