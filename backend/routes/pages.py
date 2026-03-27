"""Page-serving routes (HTML templates)."""
from __future__ import annotations

from flask import Blueprint, render_template

from backend.models.faction import FACTIONS

pages = Blueprint(
    "pages",
    __name__,
    template_folder="../../frontend/templates",
    static_folder="../../frontend/static",
    static_url_path="/static",
)


@pages.route("/")
def index():
    """Serve the main game page."""
    factions_data = [f.to_dict() for f in FACTIONS]
    return render_template("index.html", factions=factions_data)
