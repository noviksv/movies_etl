import json
import logging
from datetime import datetime, timezone
from os.path import abspath, dirname, join
from time import sleep

from backoff import backoff
from config import AppConfig, read_config_file
from elasticsearch.helpers import streaming_bulk
from etl_extractor import PostrgresExtractor, postgres_connection
from etl_loader import es_client
from storage import JsonFileStorage, State


def extract_data(config : AppConfig, **kwargs):
    with postgres_connection() as source_conn:
        query_rendered = config.sql_query.format(kwargs=kwargs)
        logging.debug(f"Sql query: {query_rendered}")
        postgres_extractor = PostrgresExtractor(
            source_conn, config.app_name, config.batch_size, query_rendered
        )
        data = postgres_extractor.extract_batch()
        for chunk in data:
            for row in chunk:
                doc = {
                    "id": row["id"],
                    "_id": row["id"],
                    "imdb_rating": row["imdb_rating"],
                    "genre": row["genre"],
                    "title": row["title"],
                    "description": row["description"],
                    "director": row["director"] if row["director"][0] is not None else [],
                    "actors_names": row["actors_names"],
                    "writers_names": row["writers_names"],
                    "actors": json.loads(row["actors"]),
                    "writers": json.loads(row["writers"]),
                }

                yield doc


@backoff()
def main(config: AppConfig) -> None:
    client = es_client()
    # working with metadata storage
    STORAGE_FILE_PATH = join(dirname(abspath(__file__)), "storage.json")
    state_storage = State(JsonFileStorage(STORAGE_FILE_PATH))
    if state_storage.get_state(config.app_name):  # storage exists
        last_max_ts = state_storage.get_state(config.app_name).get("max_ts")
    else:
        last_max_ts = "1000-01-01 00:00:00.000"

    successes = 0

    for (
        ok,
        action,
    ) in streaming_bulk(
        client=client,
        index="movies",
        actions=extract_data(config=config, last_max_ts=last_max_ts),
    ):
        successes += ok
        logging.debug("Indexed %d documents" % successes)

        if not ok:
            logging.error("Error while creating/updating index in ES.")
            logging.debug(action)

    dict_state = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "rows_updated": successes,
        "max_ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
    }
    state_storage.set_state("film_work", dict_state)


if __name__ == "__main__":
    while True:
        config = read_config_file("config.json")
        logging.basicConfig(
            level=config.loglevel, format="%(asctime)s %(levelname)s: %(message)s"
        )
        main(config=config)
        logging.info(f"Will sleep for {config.sleep_time} s")
        sleep(config.sleep_time)
