from app import create_app
from app.config import DevelopmentConfig, ProductionConfig

app = create_app(config=DevelopmentConfig)

if __name__ == "__main__":
    app.run(debug=True)