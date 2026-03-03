"""
Manipulação centralizada de erros para a aplicação.
Fornece handlers consistentes e decoradores para tratamento de exceções.
"""

from flask import jsonify, render_template
from werkzeug.exceptions import HTTPException
import logging
from functools import wraps

# Configurar logger
logger = logging.getLogger(__name__)


class APIError(Exception):
    """Classe base para erros da API"""
    
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        rv['status_code'] = self.status_code
        return rv


class ValidationError(APIError):
    """Erro de validação de dados"""
    def __init__(self, message, details=None):
        super().__init__(message, 400)
        self.details = details or {}
    
    def to_dict(self):
        rv = super().to_dict()
        if self.details:
            rv['details'] = self.details
        return rv


class NotFoundError(APIError):
    """Recurso não encontrado"""
    def __init__(self, message="Recurso não encontrado"):
        super().__init__(message, 404)


class UnauthorizedError(APIError):
    """Não autorizado"""
    def __init__(self, message="Você precisa estar autenticado"):
        super().__init__(message, 401)


class ForbiddenError(APIError):
    """Acesso proibido"""
    def __init__(self, message="Acesso proibido"):
        super().__init__(message, 403)


class ConflictError(APIError):
    """Conflito (ex: recurso duplicado)"""
    def __init__(self, message="Conflito: recurso já existe"):
        super().__init__(message, 409)


def handle_api_error(error):
    """Handler para erros da API"""
    response = error.to_dict()
    return jsonify(response), error.status_code


def handle_http_error(error):
    """Handler para erros HTTP padrão"""
    response = {
        'error': error.description or str(error),
        'status_code': error.code,
        'type': error.__class__.__name__
    }
    return jsonify(response), error.code


def handle_generic_error(error):
    """Handler para exceções genéricas"""
    logger.error(f"Erro não tratado: {str(error)}", exc_info=True)
    response = {
        'error': 'Erro interno do servidor',
        'status_code': 500,
        'type': 'InternalServerError'
    }
    return jsonify(response), 500


def handle_database_error(error):
    """Handler para erros de banco de dados"""
    logger.error(f"Erro de banco de dados: {str(error)}", exc_info=True)
    response = {
        'error': 'Erro ao acessar banco de dados',
        'status_code': 500,
        'type': 'DatabaseError'
    }
    return jsonify(response), 500


def register_error_handlers(app):
    """
    Registra todos os manipuladores de erro na aplicação Flask.
    
    Uso em app.py:
        from errors import register_error_handlers
        register_error_handlers(app)
    """
    # Erros da API
    app.register_error_handler(APIError, handle_api_error)
    app.register_error_handler(ValidationError, handle_api_error)
    app.register_error_handler(NotFoundError, handle_api_error)
    app.register_error_handler(UnauthorizedError, handle_api_error)
    app.register_error_handler(ForbiddenError, handle_api_error)
    app.register_error_handler(ConflictError, handle_api_error)
    
    # Erros HTTP
    app.register_error_handler(HTTPException, handle_http_error)
    
    # Erros genéricos
    app.register_error_handler(Exception, handle_generic_error)
    
    # Erros específicos
    try:
        from sqlalchemy.exc import SQLAlchemyError
        app.register_error_handler(SQLAlchemyError, handle_database_error)
    except ImportError:
        pass


def catch_errors(f):
    """
    Decorator para capturar erros em rotas automaticamente.
    
    Uso:
        @blueprint.route('/endpoint')
        @catch_errors
        def my_route():
            # código aqui
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            return handle_api_error(e)
        except HTTPException as e:
            return handle_http_error(e)
        except Exception as e:
            logger.error(f"Erro em {f.__name__}: {str(e)}", exc_info=True)
            return handle_generic_error(e)
    return wrapper


def require_json(f):
    """
    Decorator para garantir que a requisição é JSON.
    
    Uso:
        @blueprint.route('/endpoint', methods=['POST'])
        @require_json
        def my_route():
            data = request.get_json()
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        from flask import request
        
        if not request.is_json:
            raise ValidationError(
                "Content-Type deve ser application/json",
                {'content_type': request.content_type}
            )
        return f(*args, **kwargs)
    return wrapper


class ErrorResponse:
    """Classe auxiliar para criar respostas de erro padronizadas"""
    
    @staticmethod
    def json(message, status_code=400, details=None):
        """Retorna erro em formato JSON"""
        response = {
            'error': message,
            'status_code': status_code
        }
        if details:
            response['details'] = details
        return jsonify(response), status_code
    
    @staticmethod
    def validation(message, details):
        """Retorna erro de validação"""
        response = {
            'error': 'Erro de validação',
            'message': message,
            'details': details
        }
        return jsonify(response), 400
    
    @staticmethod
    def not_found(message="Recurso não encontrado"):
        """Retorna erro 404"""
        return jsonify({'error': message}), 404
    
    @staticmethod
    def unauthorized(message="Unauthorized"):
        """Retorna erro 401"""
        return jsonify({'error': message}), 401
    
    @staticmethod
    def forbidden(message="Forbidden"):
        """Retorna erro 403"""
        return jsonify({'error': message}), 403
    
    @staticmethod
    def conflict(message="Conflict"):
        """Retorna erro 409"""
        return jsonify({'error': message}), 409
    
    @staticmethod
    def server_error(message="Erro interno do servidor"):
        """Retorna erro 500"""
        return jsonify({'error': message}), 500
