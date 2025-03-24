import os

from app import create_app
from app.config import DevelopmentConfig, ProductionConfig

os.environ["OPENAI_API_KEY"] = "rc_fd1215ca2b2883ea2b2961ae1fa53d76cae589928038009b662e85dc5bab3372"

app = create_app(config=DevelopmentConfig)
#app = get_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
