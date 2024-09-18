import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'glorp')
    DEBUG = False
    TESTING = False
    LOG_LEVEL = "INFO"
    LOGS_DIR = f'./logs/{LOG_LEVEL}.logs'
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', None)
    TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY', None)
    FEATHERLESS_API_KEY = os.environ.get('FEATHERLESS_API_KEY', None)

class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    DATABASE_URI = 'sqlite:///development.db'

class ProductionConfig(Config):
    DEBUG = False
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///production.db')

