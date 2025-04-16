import os

from dotenv import load_dotenv

from app import create_app
from app.config import DevelopmentConfig, ProductionConfig

#load_dotenv()

app = create_app(config=DevelopmentConfig)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", use_reloader=True)
