import pytest
from app import create_app 
from app.config import DevelopmentConfig
from app.infer import Infer

@pytest.fixture
def app():
    return create_app(config=DevelopmentConfig)

def test_infer(app):
    infer = Infer()
    assert infer._gen("How are you", "You are a helpful AI", "groq")