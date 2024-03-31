import pymongo
import subprocess
import sys
from pymongo.errors import ConnectionFailure
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging

class EastablishMongoDBConnection:
    def __init__(self):
        self.connection_string = "mongodb://localhost:27017"
        self.logger = OCRREngineLogging().configure_logger()

    def establish_connection(self):
        try:
            client = pymongo.MongoClient(self.connection_string)
            client.admin.command('ping')
            return client
        except ConnectionFailure as e:
            self.logger.error(f"| Failed to establish a connection to MongoDB: {e}")
            sys.exit(1)