from flask import Blueprint

bp = Blueprint('tutor', __name__, url_prefix='/tutor')

from app.tutor import routes