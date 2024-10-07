from loguru import logger
from dotenv import load_dotenv
import os
import sys

load_dotenv()

logger.remove()

log_file = os.getenv('LOG_FILE', 'sync.log')

logger.add(log_file, rotation='1 MB', level="INFO")

logger.add(sys.stdout, level='INFO')
