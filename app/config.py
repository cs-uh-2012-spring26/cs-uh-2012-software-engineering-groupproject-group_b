import logging
from os import environ

from dotenv import load_dotenv


def get_required_environ(name: str) -> str:
    load_dotenv(override=False)
    try:
        value = environ[name]
    except KeyError as e:
        logging.fatal(f"Environment variable {e} is required.")
        raise KeyError

    if len(value.strip()) == 0:
        raise ValueError(f"Required environment variable {name} cannot be empty")
    return value


class Config(object):
    MONGO_URI = get_required_environ("MONGO_URI")
    DB_NAME = get_required_environ("DB_NAME")
    MOCK_DB = get_required_environ("MOCK_DB").lower() == "true"
    DEBUG = get_required_environ("DEBUG").lower() == "true"
    JWT_SECRET_KEY = get_required_environ("JWT_SECRET_KEY")
    AWS_ACCESS_KEY_ID = get_required_environ("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = get_required_environ("AWS_SECRET_ACCESS_KEY")
    AWS_SES_REGION = get_required_environ("AWS_SES_REGION")
    SES_SENDER_EMAIL = get_required_environ("SES_SENDER_EMAIL")
    TELEGRAM_BOT_TOKEN = get_required_environ("TELEGRAM_BOT_TOKEN")

class TestConfig(object):
    MOCK_DB = True
    MONGO_URI = "mongodb://localhost:27017"
    DB_NAME = "test_db"
    JWT_SECRET_KEY = get_required_environ("JWT_SECRET_KEY")
    DEBUG = True