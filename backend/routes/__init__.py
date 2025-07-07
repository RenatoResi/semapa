from .arvore import arvore_bp
from .requerente import requerente_bp
from .requerimento import requerimento_bp
from .ordem_servico import ordem_servico_bp

# Opcional: crie uma lista para facilitar o registro em lote
all_blueprints = [
    arvore_bp,
    requerente_bp,
    requerimento_bp,
    ordem_servico_bp
]
