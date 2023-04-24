import json

from pydantic import BaseModel


class PostgresConfig(BaseModel):
    db_host: str
    db_name: str
    db_user: str
    db_password: str
    db_port: int


class ElasticConfig(BaseModel):
    els_host: str
    els_port: int


class AppConfig(BaseModel):
    app_name: str
    app_version: float
    postgres_settings: PostgresConfig
    elastic_settings: ElasticConfig
    sql_query: str
    batch_size: int
    sleep_time: int
    loglevel: str


def read_config_file(file_path: str) -> AppConfig:
    with open(file_path, "r") as f:
        config_data = json.load(f)
    return AppConfig(**config_data)

