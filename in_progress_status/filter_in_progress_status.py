import configparser
from config.mongodb_connection import EastablishMongoDBConnection
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from time import sleep
import os
import requests
import json

class FilterInProgressStatusDocuments:
    def __init__(self, doc_upload_path: str, in_progress_status_q: object) -> None:
        self.doc_upload_path = doc_upload_path
        self.in_progress_status_q = in_progress_status_q
        self.db_connection = EastablishMongoDBConnection()
        self.logger = OCRREngineLogging().configure_logger()
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(r'C:\Program Files (x86)\OCRR\config\configuration.ini')
        self.doc_upload_path = config['Paths']['upload']
    
    def _establish_db_connection(self):
        try:
            self.db_client = self.db_connection.establish_connection()
            self.collection_filedetails = self.db_client["upload"]["fileDetails"]
            self.collection_ocrr = self.db_client["ocrrworkspace"]["ocrr"]
        except Exception as e:
            self.logger.error(f"| Establishing MongoDB connection: {e}")

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
                    if self._check_file_path_exits(document['uploadDir']) and self._check_file_extenstion(document['fileExtension']) :
                        self.insert_in_progress_status_doc_info(document)
                    else:
                        self._update_status_invalid_file(document['taskId'], document['uploadDir'])
                        #self._webhook_post_request(document['taskId'])
                sleep(5)
        except Exception as e:
            self.logger.error(f"| While querying IN_PROGRESS status: {e}")
    
    def insert_in_progress_status_doc_info(self, document):
        try:
            taskid = document['taskId']
            if self._check_existing_taskid(taskid):
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
                self._update_in_progress_status(taskid)
        except Exception as e:
            self.logger.error(f"| Inserting IN_PROGRESS status document info.: {e}")
    
    def _check_existing_taskid(self, taskid: str) -> bool:
        try:
            return not self.collection_ocrr.find_one({"taskId": taskid})
        except Exception as e:
            self.logger.error(f"| Checking existing task ID: {e}")
    
    def _update_in_progress_status(self, taskid: str):
        try:
            self.collection_filedetails.update_one({"taskId": taskid}, {"$set": {"status": "IN_QUEUE"}})
        except Exception as  e:
            self.logger.error(f"| Updating IN_PROGRESS status: {e}")
    
    def _check_file_path_exits(self, filepath: str) -> bool:
        if not os.path.exists(f"{self.doc_upload_path}\\{filepath}"):
            return False
        return True
    
    def _check_file_extenstion(self, fileextension: str) -> bool:
        if fileextension.lower() not in ['jpeg', 'jpg']:
            self.logger.error(f"| Invalid File extention: {fileextension}")
            return False
        return True
    
    def _update_status_invalid_file(self, taskid: str, filepath: str):
        query = {"taskId": taskid}
        update = {
            "$set": {
                "status": "REJECTED",
                "taskResult": "Invalid Document file"
                }
            }
        self.collection_filedetails.update_one(query, update)
        self.logger.error(f"| Invalid Document file: {filepath}")
    
    def _webhook_post_request(self, taskid):
        taskid_to_filter = {"taskId": taskid}
        result = self.collection_filedetails.find_one(taskid_to_filter)
        client_id = result['clientId']
        payload = {
            "taskId": result['taskId'],
            "status": result["status"],
            "taskResult": result["taskResult"],
            "clientId": result["clientId"],
            "uploadDir": result["uploadDir"]
        }

        """Get Client Webhook URL from webhook DB"""
        collection_webhooks = self.db_client["upload"]["webhooks"]
        filter_query = {"clientId": client_id}
        client_doc = collection_webhooks.find_one(filter_query)
        if client_doc:
            WEBHOOK_URL = client_doc["url"]
            HEADER = {'Content-Type': 'application/json'}
            response = requests.post(WEBHOOK_URL+"/CVCore/processstatus", data=json.dumps(payload), headers=HEADER)
            if response.status_code != 200:
                self.logger.error(f"| Connecting to WebHOOK: {response.status_code}")
            else:
                self.logger.info(f"| Webhook POST request successful: {client_id}")
        else:
            self.logger.error(f"| Webhook clientid not found")
