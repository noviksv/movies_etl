import json
import logging
from datetime import datetime, timezone
from os.path import abspath, dirname, join
from time import sleep

from backoff import backoff
from config import AppConfig, read_config_file, create_model_instance
from elasticsearch.helpers import streaming_bulk
from etl_extractor import PostrgresExtractor, postgres_connection
from etl_loader import es_client
from storage import JsonFileStorage, State


def extract_data(config : AppConfig, transfer_number, **kwargs):
    with postgres_connection() as source_conn:
        query_rendered = config.transfer_list[transfer_number].sql_query.format(kwargs=kwargs)
        logging.debug(f"Sql query: {query_rendered}")
        postgres_extractor = PostrgresExtractor(
            source_conn, config.app_name, config.transfer_list[transfer_number].batch_size, query_rendered
        )
        data = postgres_extractor.extract_batch()
        for chunk in data:
            for row in chunk:
                Doc = create_model_instance(config.transfer_list[transfer_number].pydantic_class)
                try:
                    doc = Doc.parse_obj(row)
                except(Exception) as e:
                    logging.debug(row)
                    logging.exception('{0}'.format(e))

                doc_temp = doc.dict()
                doc_temp["_id"] = row['id']
                if "uuid" in doc_temp.keys():
                    doc_temp["UUID"] = doc_temp.pop("uuid")

                yield doc_temp


@backoff()
def main(config: AppConfig, transfer_number) -> None:
    client = es_client()
    # working with metadata storage
    STORAGE_FILE_PATH = join(dirname(abspath(__file__)), "storage.json")
    state_storage = State(JsonFileStorage(STORAGE_FILE_PATH))
    if state_storage.get_state(config.transfer_list[transfer_number].es_index):  # storage exists
        last_max_ts = state_storage.get_state(config.transfer_list[transfer_number].es_index).get("max_ts")
    else:
        last_max_ts = "1000-01-01 00:00:00.000"

    successes = 0

    for (
        ok,
        action,
    ) in streaming_bulk(
        client=client,
        index=config.transfer_list[transfer_number].es_index,
        actions=extract_data(config=config, transfer_number=transfer_number, last_max_ts=last_max_ts),
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
    state_storage.set_state(config.transfer_list[transfer_number].es_index, dict_state)


if __name__ == "__main__":
    while True:
        config = read_config_file("config.json")
        logging.basicConfig(
            level=config.loglevel, format="%(asctime)s %(levelname)s: %(message)s"
        )
        for n, _ in enumerate(config.transfer_list):
            print(n)
            main(config=config, transfer_number=n)
            logging.info(f"Will sleep for {config.transfer_list[0].sleep_time} s")
            sleep(config.transfer_list[0].sleep_time)
