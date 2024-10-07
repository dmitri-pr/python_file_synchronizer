import requests
from logger_config import logger


class YandexDisk:
    """
    Класс, служащий для взаимодействия с API Яндекс Диска
    """
    def __init__(self, token, backup_folder):
        self.token = token
        self.backup_folder = backup_folder
        self.base_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.headers = {
            'Authorization': f'OAuth {self.token}',
        }
        self.conn_err = False

    def load(self, path: str, filename: str) -> None:
        """Загрузка файла в облако."""
        try:
            response = requests.get(
                f'{self.base_url}/upload?path={self.backup_folder}/{filename}'
                f'&overwrite=true', headers=self.headers
            )
            response.raise_for_status()
            upload_url = response.json().get('href')
            with open(path, 'rb') as file:
                upload_response = requests.put(upload_url, files={'file': file})
                upload_response.raise_for_status()
            logger.info(f'Файл {path} успешно загружен в облако.')
            self.conn_err = False
        except Exception as error:
            logger.error(f'Ошибка при загрузке файла {path} в облако: {error}.')
            self.conn_err = True

    def reload(self, path: str, filename: str) -> None:
        """Перезапись файла в облаке."""
        self.load(path, filename)

    def move(self, old_name: str, new_name: str) -> None:
        """Изменение названия файла в облаке."""
        try:
            response = requests.post(
                f'{self.base_url}/move?from={self.backup_folder}/{old_name}'
                f'&path={self.backup_folder}/{new_name}', headers=self.headers
            )
            response.raise_for_status()
            logger.info(
                f'Название файла {old_name} успешно изменено в облаке на {new_name}.'
            )
            self.conn_err = False
        except Exception as error:
            logger.error(
                f'Ошибка при изменении названия файла {old_name} в облаке: {error}.'
            )
            self.conn_err = True

    def delete(self, file: str) -> None:
        """Удаление файла из облака."""
        try:
            response = requests.delete(
                f'{self.base_url}?path={self.backup_folder}/{file}', headers=self.headers
            )
            response.raise_for_status()
            logger.info(f'Файл {file} успешно удалён из облака.')
            self.conn_err = False
        except Exception as error:
            logger.error(f'Ошибка при удалении файла {file} из облака: {error}.')
            self.conn_err = True

    def get_info(self) -> dict | None:
        """Получение информации о файлах в облаке."""
        try:
            response = requests.get(
                f'{self.base_url}?path={self.backup_folder}', headers=self.headers
            )
            response.raise_for_status()
            self.conn_err = False
            logger.info(f'Информация о файлах в облаке получена.')
            return response.json()
        except Exception as error:
            logger.error(f'Ошибка при получении информации о файлах в облаке: {error}.')
            self.conn_err = True
            return None
