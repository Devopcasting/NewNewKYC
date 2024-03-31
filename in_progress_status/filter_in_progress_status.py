from config.mongodb_connection import EastablishMongoDBConnection
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from time import sleep
import sys

class FilterInProgressStatusDocuments:
    def __init__(self, doc_upload_path: str, in_progress_status_q: object) -> None:
        self.doc_upload_path = doc_upload_path
        self.in_progress_status_q = in_progress_status_q
        self.db_connection = EastablishMongoDBConnection()
        self.logger = OCRREngineLogging().configure_logger()
    
    def _establish_db_connection(self):
        try:
            db_client = self.db_connection.establish_connection()
            self.collection_filedetails = db_client["upload"]["fileDetails"]
            self.collection_ocrr = db_client["ocrrworkspace"]["ocrr"]
        except Exception as e:
            self.logger.error(f"| Establishing MongoDB connection: {e}")
            sys.exit(1)

    def _get_document_path(self, document):
        document_path_list = [part for part in document['uploadDir'].split('/') if part]
        document_sub_path = '\\'.join(document_path_list)
        return f"{self.doc_upload_path}\\{document_sub_path}"
    
    def query_in_progress_status(self):
        try:
            self._establish_db_connection()
            while True:
                documents = self.collection_filedetails.find({"status": "IN_PROGRESS"})
                for document in documents:
                    #document_path = self._get_document_path(document)
                    self.insert_in_progress_status_doc_info(document)
                sleep(5)
        except Exception as e:
            self.logger.error(f"| While querying IN_PROGRESS status: {e}")
            sys.exit(1)
    
    def insert_in_progress_status_doc_info(self, document):
        try:
            taskid = document['taskId']
            if self.check_existing_taskid(taskid):
                document_info = {
                    "taskId": taskid,
                    "path": self._get_document_path(document),
                    "status": document['status'],
                    "clientId": document['clientId'],
                    "taskResult": "",
                    "uploadDir": document['uploadDir']
                }
                self.collection_ocrr.insert_one(document_info)
                self.in_progress_status_q.put(document_info)
                self.update_in_progress_status(taskid)
        except Exception as e:
            self.logger.error(f"| Inserting IN_PROGRESS status document info.: {e}")
            sys.exit(1)
    
    def check_existing_taskid(self, taskid: str) -> bool:
        try:
            return not self.collection_ocrr.find_one({"taskId": taskid})
        except Exception as e:
            self.logger.error(f"| Checking existing task ID: {e}")
            sys.exit(1)
    
    def update_in_progress_status(self, taskid: str):
        try:
            self.collection_filedetails.update_one({"taskId": taskid}, {"$set": {"status": "IN_QUEUE"}})
        except Exception as  e:
            self.logger.error(f"| Updating IN_PROGRESS status: {e}")
            sys.exit(1)
        
