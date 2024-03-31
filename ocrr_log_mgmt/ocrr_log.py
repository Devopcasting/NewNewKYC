import logging
import configparser
import os

class OCRREngineLogging:
    def __init__(self, log_file='ocrr.log', log_level=logging.INFO):
        self.log_file = os.path.join(self._get_log_path(), log_file)
        self.log_level = log_level

    def configure_logger(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(self.log_level)

        if not self._file_handler_exists(logger):
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(self.log_level)
            formatter = logging.Formatter('%(process)d %(asctime)s %(levelname)s %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def _get_log_path(self):
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(r'C:\Program Files (x86)\OCRR\config\configuration.ini')
        return config['Paths']['logs'] if 'Paths' in config else os.getcwd()

    def _file_handler_exists(self, logger):
        return any(isinstance(handler, logging.FileHandler) and handler.baseFilename == self.log_file for handler in logger.handlers)