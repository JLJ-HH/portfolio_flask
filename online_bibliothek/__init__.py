from flask import Blueprint

online_bibliothek_bp = Blueprint(
    'online_bibliothek',
    __name__,
    template_folder='templates',
    static_folder='static'
)

from . import routes
