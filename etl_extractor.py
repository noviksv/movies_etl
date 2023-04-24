import logging
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Generator

from config import read_config_file


@contextmanager
def postgres_connection() -> Generator:
    # Connect to the Postgres database
    config = read_config_file("config.json")
    dsl = {
        "dbname": config.postgres_settings.db_name,
        "user": config.postgres_settings.db_user,
        "password": config.postgres_settings.db_password,
        "host": config.postgres_settings.db_host,
        "port": str(config.postgres_settings.db_port),
    }
    logging.debug(dsl)
    conn = psycopg2.connect(**dsl)
    yield conn
    # Close the Postgres database connection
    conn.close()


class PostrgresExtractor:
    def __init__(self, connection: Generator, source_table: str, batch_size : int, query: str) -> None:
        self.connection = connection
        self.source_table = source_table
        self.batch_size = batch_size
        self.query = query

    def extract_batch(self) -> Generator:
        """Extracts data by batches"""
        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        logging.debug(self.query)
        try:
            cursor.execute(self.query)
            while data := cursor.fetchmany(self.batch_size): 
                logging.debug(f"Readed next batch {len(data)} rows") 
                yield data 
        except (psycopg2.InterfaceError, psycopg2.OperationalError) as e:
            logging.exception('{0}'.format(e))
            logging.error(f"Failed to read data from {self.source_table}: {e}")
