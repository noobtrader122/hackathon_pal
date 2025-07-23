from flask import Blueprint, render_template
from ..models.sqlalchemy_models import Hackathon, Challenge

hackathon_bp = Blueprint("hackathon_bp", __name__)

# routes/hackathon_bp.py (example usage)
@hackathon_bp.route('/<int:hid>')
def hackathon_page(hid):
    hackathon = Hackathon.query.get_or_404(hid)
    challenges = Challenge.query.filter_by(hackathon_id=hid).order_by(Challenge.id).all()
    # If you track user progress, add .solved fields here
    return render_template("index.html", hackathon=hackathon, challenges=challenges)

