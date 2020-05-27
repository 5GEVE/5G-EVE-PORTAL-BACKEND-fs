from app import create_app
import os, ssl

basedir = os.path.abspath(os.path.dirname(__file__))

app=create_app()

app.run(host='0.0.0.0', port='9191')