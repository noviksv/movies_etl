import json
from pydantic import BaseModel, Field, validator
from typing import Type

class PostgresConfig(BaseModel):
    db_host: str
    db_name: str
    db_user: str
    db_password: str
    db_port: int


class ElasticConfig(BaseModel):
    els_host: str
    els_port: int


class TransferList(BaseModel):
    transfer_name: str
    sql_query: str
    es_index: str
    sleep_time: int
    batch_size: int
    pydantic_class: str


class AppConfig(BaseModel):
    app_name: str
    app_version: float
    postgres_settings: PostgresConfig
    elastic_settings: ElasticConfig
    transfer_list: list[TransferList]
    loglevel: str


class Doc(BaseModel):
    id: str = Field('id')
    imdb_rating: float | None = Field('imdb_rating')
    genre: list[str] = Field('genre')
    title: str = Field("title")
    description: str | None = Field("description")
    creation_date: str | None = Field("creation_date")
    director: list[str | None] | None = Field("director")
    actors_names: list[str | None] | None = Field("actors_names")
    writers_names: list[ str | None] | None = Field("writers_names")
    directors: list[dict | None] | None =Field("directors")
    actors: list[dict | None] | None =Field("actors")
    writers: list [dict | None] | None = Field("writers")
    genres: list [dict | None] | None = Field("genres")
    
        
    @validator('directors', pre=True)
    def parse_directors(cls, value):
        return json.loads(value)
    
    @validator('actors', pre=True)
    def parse_actors(cls, value):
        return json.loads(value)
    
    @validator('genres', pre=True)
    def parse_genres(cls, value):
        return json.loads(value)
    
    @validator('writers', pre=True)
    def parse_writers(cls, value):
        return json.loads(value)
    
    @validator('director', pre=True)
    def parse_director(cls, value):
        return value if value[0] is not None else []


class Person(BaseModel):
    uuid: str = Field('id')
    full_name: str | None = Field('full_name')
    films: list [dict | None] | None = Field('films')

    @validator('films', pre=True)
    def parse_films(cls, value):
        return json.loads(value)


class Genre(BaseModel):
    uuid: str = Field('id')
    name: str | None = Field('name')


def read_config_file(file_path: str) -> AppConfig:
    with open(file_path, "r") as f:
        config_data = json.load(f)
    return AppConfig(**config_data)


def create_model_instance(model_name: str) -> Type[BaseModel]:
    model_class = globals().get(model_name)
    if not model_class or not issubclass(model_class, BaseModel):
        raise ValueError(f"{model_name} is not a valid Pydantic model class.")
    return model_class(name="example")