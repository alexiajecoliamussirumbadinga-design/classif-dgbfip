# ============================================================
# Point d'entrée WSGI pour la production (gunicorn wsgi:app)
# Permet `gunicorn wsgi:app` depuis la racine du dépôt,
# sans dépendre de --chdir.
# ============================================================
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from app_FINAL import app  # noqa: E402

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
