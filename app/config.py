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

class Model:
    def __init__(self, name: str):
        self.groq_models = [
            "deepseek-r1-distill-llama-70b", 
            "qwen-qwq-32b", 
            "gemma2-9b-it", 
            "llama-3.3-70b-versatile", 
            "meta-llama/llama-4-maverick-17b-128e-instruct", 
            "meta-llama/llama-4-maverick-17b-128e-instruct"
        ]
        self.name = name
        self.backend = self._get_backend()

    def set_client(self, client):
        self.client = client

    def _get_backend(self) -> str:
        if self.name in self.groq_models:
            return "groq"
        else:
            return "featherless"

    def __str__(self):
        return f"Model(name: {self.name}, backend: {self.backend})"

class Keys:
    def __init__(self, groq_key: str, feather_key: str):
        self.groq_key = groq_key
        self.feather_key = feather_key

class ModuleConfig:
    MAX_INFER_TRIES = int(os.environ.get("MAX_INFER_TRIES"))

    def __init__(self, default_model: Model, keys: Keys):
        self.DEFAULT_MODEL = default_model
        self.KEYS = keys

class CoreConfig(ModuleConfig):
    CORE_MODEL = Model(os.environ.get("CORE_MODEL"))
    CORE_QUICK_MODEL = Model(os.environ.get("CORE_QUICK_MODEL"))

class HoodlemConfig(ModuleConfig):
    HOODLEM_MODEL = Model(os.environ.get("HOODLEM_MODEL"))

class NewsConfig(ModuleConfig):
    GEN_NEWS_MODEL = Model(os.environ.get("GEN_NEWS_MODEL"))
    INTERVIEW_MODEL = Model(os.environ.get("INTERVIEW_MODEL"))

class SuperintendConfig:
    KEYS = Keys(groq_key=os.environ.get("GROQ_API_KEY"), feather_key=os.environ.get("FEATHERLESS_API_KEY"))
    DEFAULT_MODEL = Model(os.environ.get("DEFAULT_MODEL"))
    CORE = CoreConfig(default_model=DEFAULT_MODEL, keys=KEYS)
    HOODLEM = HoodlemConfig(default_model=DEFAULT_MODEL, keys=KEYS)
    NEWS = NewsConfig(default_model=DEFAULT_MODEL, keys=KEYS)