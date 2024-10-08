import os
import time
import sys
import hashlib
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from logger_config import logger
from yandex_disk import YandexDisk

load_dotenv()

local_folder = os.getenv('LOCAL_FOLDER')
token = os.getenv('YANDEX_TOKEN')
backup_folder = os.getenv('BACKUP_FOLDER')


class SyncHandler(FileSystemEventHandler):
    """
    Класс, обеспечивающий обработку событий в файловой системе.
    """

    def __init__(self, yandex_disk, check_sync_func):
        self.yandex_disk = yandex_disk
        self.check_sync = check_sync_func

    def on_created(self, event):
        """
        Метод, применяющийся при создании нового файла.
        """
        filename = os.path.basename(event.src_path)
        if (
                not event.is_directory
                and not filename.startswith('~')
                and not filename.endswith('.tmp')
                and '.' in filename
        ):
            path = event.src_path
            logger.info(f'Создан файл: {path}')
            self.yandex_disk.load(path, filename)
            self.check_sync(self.yandex_disk)

    def on_modified(self, event):
        """
        Метод, применяющийся при изменении содержания файла.
        """
        filename = os.path.basename(event.src_path)
        if (
                not event.is_directory
                and not filename.startswith('~')
                and not filename.endswith('.tmp')
                and '.' in filename
        ):
            path = event.src_path
            logger.info(f'Изменён файл: {path}')
            self.yandex_disk.reload(path, filename)
            self.check_sync(self.yandex_disk)

    def on_moved(self, event):
        """
        Метод, применяющийся при переименовании файла.
        """
        old_name = os.path.basename(event.src_path)
        new_name = os.path.basename(event.dest_path)
        if (
                not event.is_directory
                and not old_name.startswith('~')
                and not new_name.startswith('~')
                and not old_name.endswith('.tmp')
                and not new_name.endswith('.tmp')
                and '.' in old_name
                and '.' in new_name
        ):
            logger.info(
                f'Изменено название файла {event.src_path}'
                f' на {event.dest_path}'
            )
            self.yandex_disk.move(old_name, new_name)
            self.check_sync(self.yandex_disk)

    def on_deleted(self, event):
        """
        Метод, применяющийся при удалении файла.
        """
        filename = os.path.basename(event.src_path)
        if (
                not event.is_directory
                and not filename.startswith('~')
                and not filename.endswith('.tmp')
                and '.' in filename
        ):
            logger.info(f'Удалён файл: {event.src_path}')
            self.yandex_disk.delete(filename)
            self.check_sync(self.yandex_disk)


def calculate_hash(file_path: str) -> str:
    """Вычисление хеша файла."""
    hash_md5 = hashlib.md5()
    filename = os.path.basename(file_path)
    if (
            file_path
            and not filename.startswith('~')
            and not filename.endswith('.tmp')) \
            and '.' in filename:
        with open(file_path, "rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


def check_sync(yandex_disk: YandexDisk) -> None:
    """
    Проверка синхронности между локальной и удаленной папками
    на тот случай, если в перерыве работы программы или вследствие
    удаления файлов в облаке возникнут расхождения в содержании
    этих папок.
    """
    local_files = {
        file: calculate_hash(os.path.join(local_folder, file))
        for file in os.listdir(local_folder)
        if not file.startswith('~')
           and not file.endswith('.tmp')
           and '.' in file
    }

    remote_info = yandex_disk.get_info()

    if remote_info and '_embedded' in remote_info and 'items' in remote_info['_embedded']:
        remote_files = {
            item['name']: item.get('md5', None)
            for item in remote_info['_embedded']['items']
        }

        for file, local_hash in local_files.items():
            if file not in remote_files:
                logger.info(f'Файл отсутствует в облаке: {file}')
                path = os.path.join(local_folder, file)
                yandex_disk.load(path, file)
            else:
                remote_hash = remote_files[file]
                if local_hash != remote_hash:
                    logger.info(f'Файл изменен: {file}, загружаем в облако.')
                    path = os.path.join(local_folder, file)
                    yandex_disk.reload(path, file)

        for file in remote_files.keys():
            if file not in local_files:
                logger.info(f'Лишний файл в облаке: {file}')
                yandex_disk.delete(file)

        logger.info(f'Файлы в локальной папке и облаке синхронизированы.')


def main():
    if not os.path.exists(local_folder):
        logger.error(f'Ошибка: Указанная папка "{local_folder}" не существует.')
        input('Неверно указана локальная папка - нажмите Enter, чтобы выйти из программы'
              ' и укажите существующую папку.')
        sys.exit(1)

    yandex_disk = YandexDisk(token, backup_folder)

    logger.info(f'Начато отслеживание изменений в "{local_folder}".')

    check_sync(yandex_disk)

    event_handler = SyncHandler(yandex_disk, check_sync)
    observer = Observer()
    observer.schedule(event_handler, local_folder, recursive=True)

    observer.start()

    try:
        while True:
            if yandex_disk.conn_err is True:
                check_sync(yandex_disk)
            time.sleep(int(os.getenv('SYNC_INTERVAL', 10)))
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
    logger.info(f'Закончено отслеживание изменений в "{local_folder}".')


if __name__ == "__main__":
    main()
