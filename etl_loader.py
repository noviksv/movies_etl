from config import read_config_file
from elasticsearch import Elasticsearch


def es_client() -> Elasticsearch:
    config = read_config_file("config.json")
    return Elasticsearch(
        hosts=f"http://{config.elastic_settings.els_host}:{config.elastic_settings.els_port}"
    )
