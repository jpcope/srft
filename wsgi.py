"""
Application entry point for a production-level WSGI server. It'll import our
app module from our app package, which will contain all our actual logic.
"""

from app import app

application = app
