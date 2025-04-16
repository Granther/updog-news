import os
import sys

from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'glorp')
    DEBUG = False
    TESTING = False
    LOG_LEVEL = "INFO"
    LOGS_DIR = f'./logs/{LOG_LEVEL}.logs'
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', None)
    TAVILY_API_KEY = os.getenv('TAVILY_API_KEY', None)
    FEATHERLESS_API_KEY = os.getenv('FEATHERLESS_API_KEY', None)

class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    DATABASE_URI = 'sqlite:///development.db'

class ProductionConfig(Config):
    DEBUG = False
    DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///production.db')

class Model:
    def __init__(self, name: str):
        self.groq_models = [
            "deepseek-r1-distill-llama-70b", 
            "qwen-qwq-32b", 
            "gemma2-9b-it", 
            "llama-3.3-70b-versatile", 
            "meta-llama/llama-4-maverick-17b-128e-instruct", 
            "meta-llama/llama-4-scout-17b-16e-instruct"
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
    def __init__(self):
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        self.FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY")

        if self.GROQ_API_KEY is None or self.FEATHERLESS_API_KEY is None:
            raise Exception("Needed API Keys not found in .env for Keys()")

class ModuleConfig:
    MAX_INFER_TRIES = int(os.getenv("MAX_INFER_TRIES"))

    def __init__(self, default_model: Model, keys: Keys):
        self.DEFAULT_MODEL = default_model
        self.KEYS = keys

class CoreConfig(ModuleConfig):
    CORE_MODEL = Model(os.getenv("CORE_MODEL"))
    CORE_QUICK_MODEL = Model(os.getenv("CORE_QUICK_MODEL"))
    CHROMA_PATH = os.getenv("CHROMA_PATH")

    def __str__(self):
        return f"--- Core Config ---\nMain Model: {self.CORE_MODEL}\nQuick Model: {self.CORE_QUICK_MODEL}\nChroma Path: {self.CHROMA_PATH}"

class HoodlemConfig(ModuleConfig):
    HOODLEM_MODEL = Model(os.getenv("HOODLEM_MODEL"))
    
    def __str__(self):
        return f"--- Hoodlem Config ---\nChat Model: {self.HOODLEM_MODEL}"

class NewsConfig(ModuleConfig):
    GEN_NEWS_MODEL = Model(os.getenv("GEN_NEWS_MODEL"))
    INTERVIEW_MODEL = Model(os.getenv("INTERVIEW_MODEL"))

    def __str__(self):
        return f"--- News Config ---\nGen News Model: {self.GEN_NEWS_MODEL}\nInterview Model: {self.INTERVIEW_MODEL}"

class SuperintendConfig:
    try:
        KEYS = Keys()
        DEFAULT_MODEL = Model(os.getenv("DEFAULT_MODEL"))
        CORE = CoreConfig(default_model=DEFAULT_MODEL, keys=KEYS)
        HOODLEM = HoodlemConfig(default_model=DEFAULT_MODEL, keys=KEYS)
        NEWS = NewsConfig(default_model=DEFAULT_MODEL, keys=KEYS)
    except Exception as e:
        print(f"Fatal error occured while instantiating Superintend Config or its required children: {e}", file=sys.stderr)
        sys.exit(1)

    def __str__(self):
        return f"\t=== Superintend Config ===\nDefault Model: {self.DEFAULT_MODEL}\n{self.CORE}\n{self.HOODLEM}\n{self.NEWS}"