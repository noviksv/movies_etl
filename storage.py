import abc
import json
from typing import Any


class BaseStorage(abc.ABC):
    """Абстрактное хранилище состояния.

    Позволяет сохранять и получать состояние.
    Способ хранения состояния может варьироваться в зависимости
    от итоговой реализации. Например, можно хранить информацию
    в базе данных или в распределённом файловом хранилище.
    """

    @abc.abstractmethod
    def save_state(self, state: dict[str, Any]) -> None:
        """Сохранить состояние в хранилище."""

    @abc.abstractmethod
    def retrieve_state(self) -> dict[str, Any]:
        """Получить состояние из хранилища."""


class JsonFileStorage(BaseStorage):
    """Реализация хранилища, использующего локальный файл."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def save_state(self, state: dict[str, Any]) -> None:
        """Сохранить состояние в хранилище."""
        state = self.retrieve_state() | state
        json_object = json.dumps(state, indent=4)
        # Writing to sample.json
        with open(self.file_path, "w") as outfile:
            outfile.write(json_object)

    def retrieve_state(self) -> dict[str, Any]:
        """Получить состояние из хранилища."""
        # Opening JSON file
        from os.path import exists

        if exists(self.file_path):
            with open(self.file_path, "r") as openfile:
                # Reading from json file
                json_object = json.load(openfile)
            return json_object
        return {}


class State:
    """Класс для работы с состояниями."""

    def __init__(self, storage: BaseStorage) -> None:
        self.storage = storage

    def set_state(self, key: str, value: Any) -> None:
        """Установить состояние для определённого ключа."""
        self.storage.save_state({key: value})

    def get_state(self, key: str) -> Any:
        """Получить состояние по определённому ключу."""
        a = self.storage.retrieve_state()
        return a.get(key, None)

