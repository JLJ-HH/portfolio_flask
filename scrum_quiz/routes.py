from flask import Blueprint, render_template

scrum_quiz_bp = Blueprint('scrum_quiz', __name__, 
                           template_folder='templates', 
                           static_folder='static')

@scrum_quiz_bp.route("/")
def index():
    """Renders the main Scrum Quiz interface."""
    return render_template("scrum_quiz/index.html")
