import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError, RequestException
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
                f'&overwrite=true', headers=self.headers, timeout=5
            )
            response.raise_for_status()
            upload_url = response.json().get('href')
            with open(path, 'rb') as file:
                upload_response = requests.put(
                    upload_url, files={'file': file}, timeout=5
                )
                upload_response.raise_for_status()
            logger.info(f'Файл {path} успешно загружен в облако.')
            self.conn_err = False
        except (ConnectionError, Timeout):
            logger.error(f'Файл {path} не загружен в облако: ошибка соединения или'
                         f' превышено время ожидания.')
            self.conn_err = True
        except HTTPError as error:
            logger.error(f'Файл {path} не загружен в облако: ошибка HTTP с кодом'
                         f' {error.response.status_code}.')
            if error.response.status_code == 404:
                logger.info(f'Возможно неверно указана облачная папка - укажите верную'
                            f' папку и перезапустите программу.')
            self.conn_err = True
        except RequestException as error:
            logger.error(f'Файл {path} не загружен в облако. Ошибка: {error}.')
            self.conn_err = True
        except (FileNotFoundError, PermissionError):
            logger.info(f'Попытка загрузки в облако временного файла {path}.')

    def reload(self, path: str, filename: str) -> None:
        """Перезапись файла в облаке."""
        self.load(path, filename)

    def move(self, old_name: str, new_name: str) -> None:
        """Изменение названия файла в облаке."""
        try:
            response = requests.post(
                f'{self.base_url}/move?from={self.backup_folder}/{old_name}'
                f'&path={self.backup_folder}/{new_name}', headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            logger.info(
                f'Название файла {old_name} успешно изменено в облаке на {new_name}.'
            )
            self.conn_err = False
        except (ConnectionError, Timeout):
            logger.error(f'Файл {old_name} не изменен в облаке: ошибка соединения или'
                         f' превышено время ожидания.')
            self.conn_err = True
        except HTTPError as error:
            logger.error(f'Файл {old_name} не изменен в облаке: ошибка HTTP с кодом'
                         f' {error.response.status_code}.')
            if error.response.status_code == 404:
                logger.info(f'Возможно неверно указана облачная папка - укажите верную'
                            f' папку и перезапустите программу.')
            self.conn_err = True
        except RequestException as error:
            logger.error(f'Файл {old_name} не изменен в облаке. Ошибка: {error}.')
            self.conn_err = True
        except (FileNotFoundError, PermissionError):
            logger.info(f'Попытка изменения названия временного файла {old_name} в облаке.')

    def delete(self, file: str) -> None:
        """Удаление файла из облака."""
        try:
            response = requests.delete(
                f'{self.base_url}?path={self.backup_folder}/{file}', headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            logger.info(f'Файл {file} успешно удалён из облака.')
            self.conn_err = False
        except (ConnectionError, Timeout):
            logger.error(f'Файл {file} не удален из облака: ошибка соединения или'
                         f' превышено время ожидания.')
            self.conn_err = True
        except HTTPError as error:
            logger.error(f'Файл {file} не удален из облака: ошибка HTTP с кодом'
                         f' {error.response.status_code}.')
            if error.response.status_code == 404:
                logger.info(f'Возможно неверно указана облачная папка - укажите верную'
                            f' папку и перезапустите программу.')
            self.conn_err = True
        except RequestException as error:
            logger.error(f'Файл {file} не удален из облака. Ошибка: {error}.')
            self.conn_err = True
        except (FileNotFoundError, PermissionError):
            logger.info(f'Попытка удаления в облаке временного файла {file}.')

    def get_info(self) -> dict | None:
        """Получение информации о файлах в облаке."""
        try:
            response = requests.get(
                f'{self.base_url}?path={self.backup_folder}', headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            self.conn_err = False
            logger.info(f'Информация о файлах в облаке получена.')
            return response.json()
        except (ConnectionError, Timeout):
            logger.error(f'Информация о файлах не получена из облака: ошибка соединения'
                         f' или превышено время ожидания.')
            self.conn_err = True
            return None
        except HTTPError as error:
            logger.error(f'Информация о файлах не получена из облака: ошибка HTTP с кодом'
                         f' {error.response.status_code}.')
            if error.response.status_code == 404:
                logger.info(f'Возможно неверно указана облачная папка - укажите верную'
                            f' папку и перезапустите программу.')
            self.conn_err = True
            return None
        except RequestException as error:
            logger.error(f'Информация о файлах не получена из облака. Ошибка: {error}.')
            self.conn_err = True
            return None
