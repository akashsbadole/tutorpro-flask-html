from flask import Blueprint

bp = Blueprint('course', __name__,
               template_folder='templates',
               url_prefix='/course')

from app.course import routes
from app.course import syllabus
from app.course import assignments
from app.course import progress
from app.course import interactive
from app.course import api