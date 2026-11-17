"""
Compatibility proxy for Render's default Start Command:
`gunicorn your_application.wsgi`
Forwards directly to `config.wsgi.application`.
"""

from config.wsgi import application

__all__ = ["application"]
