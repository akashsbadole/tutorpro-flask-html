from flask import Blueprint

bp = Blueprint('meeting', __name__)

from app.meeting import routes