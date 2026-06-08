import os
import pytest
from unittest.mock import patch


def test_config_loads_db_settings():
    env = {
        "DB_HOST": "myhost",
        "DB_PORT": "3307",
        "DB_NAME": "mydb",
        "DB_USER": "myuser",
        "DB_PASSWORD": "mypass",
        "LOG_LEVEL": "DEBUG",
    }
    with patch.dict(os.environ, env, clear=True):
        import importlib
        import config
        importlib.reload(config)
        assert config.DB_HOST == "myhost"
        assert config.DB_PORT == 3307
        assert config.DB_NAME == "mydb"
        assert config.DB_USER == "myuser"
        assert config.DB_PASSWORD == "mypass"
        assert config.LOG_LEVEL == "DEBUG"


def test_config_default_port():
    env = {
        "DB_HOST": "localhost",
        "DB_NAME": "gold_prices",
        "DB_USER": "root",
        "DB_PASSWORD": "pass",
    }
    with patch.dict(os.environ, env, clear=True):
        import importlib
        import config
        importlib.reload(config)
        assert config.DB_PORT == 3306
        assert config.LOG_LEVEL == "INFO"
