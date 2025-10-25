from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def nivel_requerido(*niveis_permitidos):
    """Decorador para controle de acesso por nível"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            if current_user.nivel not in niveis_permitidos:
                if current_user.nivel == 3:
                    return "<script>alert('Acesso negado'); window.location.href = '/os_listar';</script>", 403
                else:
                    flash('Acesso negado', 'error')
                    return redirect(url_for('pages.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
