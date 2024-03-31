import configparser
import threading
import queue
import sys
from config.mongodb_connection import EastablishMongoDBConnection
from in_progress_status.filter_in_progress_status import FilterInProgressStatusDocuments
from process_docs.start_processing_docs import ProcessDocuments
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging

class OCRREngine:
    def __init__(self, doc_upload_path: str, workspace_path: str) -> None:
        self.doc_upload_path = doc_upload_path
        self.workspace_path = workspace_path
        self.logger = OCRREngineLogging().configure_logger()

        try:
            self._initialize_mongodb_connection()
            self._change_upload_status()
            self.in_progress_status_q = queue.Queue()
        except Exception as e:
            self.logger.error(f"| Failed to start OCRR Engine: {e}")
            sys.exit(1)
    
    def _initialize_mongodb_connection(self):
        self.logger.info("| Starting OCRR Engine")
        try:
            db_client = EastablishMongoDBConnection().establish_connection()
            if db_client is None:
                self.logger.error("| Failed to establish connection to MongoDB")
                self.logger.info("| Stopping OCRR Engine")
                sys.exit(1)
            
            self.db_upload = db_client["upload"]
            self.db_filedetails = self.db_upload["fileDetails"]
            db_name_list = db_client.list_database_names()
            
            if "ocrrworkspace" not in db_name_list:
                self.logger.info("| Creating ocrrworkspace database and ocrr collection")
                db_client["ocrrworkspace"].create_collection("ocrr")
            else:
                self.logger.info("| Resetting ocrr collection")
                db_client["ocrrworkspace"]["ocrr"].drop()

            self.logger.info("| Connection established with MongoDB")
        except Exception as e:
            self.logger.error(f"| Error in initializing MongoDB: {e}")
            self.logger.info("| Stopping OCRR Engine")
            db_client.close()
            sys.exit(1)
        
    def _change_upload_status(self):
        self.db_filedetails.update_many({"status": "IN_QUEUE"}, {"$set": {"status": "IN_PROGRESS"}})
        self.logger.info("| Changed status 'IN_QUEUE' to 'IN_PROGRESS'")

    def start_ocrr_engine(self):
        try:
            in_progress_status_doc_thread = threading.Thread(target=self._query_in_progress_status_doc)
            process_documents_thread = threading.Thread(target=self._process_documents)

            """Start Threads"""
            in_progress_status_doc_thread.start()
            process_documents_thread.start()

            """Join Threads"""
            in_progress_status_doc_thread.join()
            process_documents_thread.join()

        except Exception as e:
            self.logger.error(f"| An error occurred during OCRR engine execution: {e}")
            sys.exit(1)

    def _query_in_progress_status_doc(self):
        filter_in_progress_status_doc = FilterInProgressStatusDocuments(self.doc_upload_path, self.in_progress_status_q)
        filter_in_progress_status_doc.query_in_progress_status()
    
    def _process_documents(self):
        process_documents = ProcessDocuments(self.in_progress_status_q, self.doc_upload_path, self.workspace_path)
        process_documents.process_docs()

if __name__ == '__main__':
    try:
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(r'C:\Program Files (x86)\OCRR\config\configuration.ini')

        doc_upload_path = config['Paths']['upload']
        workspace_path = config['Paths']['workspace']

        ocrr = OCRREngine(doc_upload_path, workspace_path)
        ocrr.start_ocrr_engine()

    except Exception as e:
        logger = OCRREngineLogging().configure_logger()
        logger.error(f"| Failed to start OCRR Engine: {e}")
        sys.exit(1)
        