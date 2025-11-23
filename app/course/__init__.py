from flask import Blueprint

bp = Blueprint('course', __name__,
               template_folder='templates',
               url_prefix='/course')

from app.course import routes