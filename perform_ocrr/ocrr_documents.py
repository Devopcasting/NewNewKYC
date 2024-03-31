import sys
import requests
import json
from config.mongodb_connection import EastablishMongoDBConnection
from document_type_identification.identify_documents import IdentifyDocumentType
from write_xml.rejected_doc_coordinates import GetRejectedDocumentCoordinates
from write_xml.rejected_document import WriteRejectedDocumentXML
from write_xml.redacted_document import WriteRedactedDocumentXML
from webhook.webhook_post_request import WebhookHandler
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from documents.cdsl.document_info import CDSLDocumentInfo
from documents.pancard.document_info import PancardDocumentInfo
from documents.aadhaarcard.e_aadhaarcard_info import EAadhaarCardDocumentInfo
from pathlib import Path

class PerformOCRROnDocuments:
    def __init__(self, document_info: dict) -> None:
        self.document_info = document_info
        self.logger = OCRREngineLogging().configure_logger()
        try:
            self.db_client = EastablishMongoDBConnection().establish_connection()
        except Exception as e:
            self.logger.error(f"| Connecting to MongoDB: {e}")
            sys.exit(1)

    def start_ocrr(self):
        try:
            docuement_identification_obj = IdentifyDocumentType(self.document_info['documentPath'])
            processing_ocrr_document_methods = [
                (docuement_identification_obj.identify_document_type("CDSL"), self._cdsl_ocrr_process),
                (docuement_identification_obj.identify_document_type("PANCARD"), self._pancard_ocrr_process),
                (docuement_identification_obj.identify_document_type("E-Aadhaar"), self._e_aadhaar_ocrr_process)
            ]
            documentIdentified = False
            """Identify document"""
            for identify_doc_method, ocrr_process in processing_ocrr_document_methods:
                if identify_doc_method:
                    self.logger.info(f"| Document identified: {self.document_info['taskId']}")
                    ocrr_process(self.document_info['documentPath'], self.document_info['redactedPath'],
                                self.document_info['documentName'], self.document_info['taskId'])
                    documentIdentified = True
                    break
            
            """Un-Identified document"""
            if not documentIdentified:
                self.logger.info(f"| Un-identified document of task id: {self.document_info['taskId']}")
                self._unidentified_document_rejected(self.document_info['documentPath'], self.document_info['redactedPath'],
                                                self.document_info['documentName'], self.document_info['taskId'])
                
            """Remove collection document from workspace ocrr"""
            self._remove_collection_doc_from_workspace_ocrr(self.document_info['taskId'])

            """Send POST request to WebHOOK"""
            # if not self._webhook_post_request(self.db_client):
            #     sys.exit(1)
            # else:
            #     self.logger.info(f"| Successfully sent webhook POST request for document task id : {self.document_info['taskId']}")
            #self._webhook_post_request(self.document_info['taskId'])

            """Close Database connection"""
            self.db_client.close()

        except Exception as e:
            self.logger.error(f"| Performing OCRR: {e}")
            sys.exit(1)
    
    def _perform_ocrr(self, status, result, document_path, redactedPath, documentName, taskid):
        if status == "REJECTED":
            """
            - Redact 80% and get the coordinates
            - Write XML for Rejected document
            """
            self.logger.info(f"| Document taskid {taskid} is REJECTED with 80% redaction")
            rejected_doc_coordinates = GetRejectedDocumentCoordinates(document_path).get_coordinates()
            WriteRejectedDocumentXML(redactedPath, documentName, rejected_doc_coordinates).writexml()
            """Update the document status"""
            self._update_document_status(taskid, "REJECTED", "Unidentified Document, 80% Redaction done")
        else:
            """Write Redacted Document XML file"""
            self.logger.info(f"| Document taskid {taskid} is REDACTED")
            redacted_doc_coordinates = result['data']
            WriteRedactedDocumentXML(redactedPath, documentName, redacted_doc_coordinates ).writexml()
            WriteRedactedDocumentXML(redactedPath, documentName, redacted_doc_coordinates ).write_redacted_data_xml()
            """Update upload db"""
            self._update_document_status(taskid, "REDACTED", result['message'])
        
        """Remove document from workspace"""
        self._remove_document_from_workspace(document_path)

    """Documents OCRR Process methods""" 
    def _cdsl_ocrr_process(self, document_path, redactedPath, documentName, taskid):
        self.logger.info(f"| Performing OCRR on CDSL docuemnt taskid: {taskid}")
        result = CDSLDocumentInfo(document_path).collect_cdsl_document_info()
        status = result['status']
        self._perform_ocrr(status, result, document_path, redactedPath, documentName, taskid)
    
    def _pancard_ocrr_process(self, document_path, redactedPath, documentName, taskid):
        self.logger.info(f"| Performing OCRR on Pancard document taskid: {taskid}")
        result = PancardDocumentInfo(document_path).collect_pancard_document_info()
        status = result['status']
        self._perform_ocrr(status, result, document_path, redactedPath, documentName, taskid)
    
    def _e_aadhaar_ocrr_process(self, document_path, redactedPath, documentName, taskid):
        self.logger.info(f"| Performing OCRR on E-Aadhaar document taskid: {taskid}")
        result = EAadhaarCardDocumentInfo(document_path).collect_e_aadhaarcard_info()
        status = result['status']
        self._perform_ocrr(status, result, document_path, redactedPath, documentName, taskid)

    
    def _remove_collection_doc_from_workspace_ocrr(self, taskid):
        database_name = "ocrrworkspace"
        collection_name = "ocrr"
        database = self.db_client[database_name]
        collection = database[collection_name]
        remove_query = {"taskId": taskid}
        collection.delete_one(remove_query)
    
    def _update_document_status(self, taskid, status, message):
        database_name = "upload"
        collection_name = "fileDetails"
        database = self.db_client[database_name]
        collection = database[collection_name]
        filter_query = {"taskId": taskid}
        update = {"$set" : {
            "status": status,
            "taskResult": message
        }}
        collection.update_one(filter_query, update)

    def _unidentified_document_rejected(self, document_path, redactedPath, documentName, taskid):
        """
            - Redact 80% and get the coordinates
            - Write XML for Rejected document
        """
        rejected_doc_coordinates = GetRejectedDocumentCoordinates(document_path).get_coordinates()
        WriteRejectedDocumentXML(redactedPath, documentName, rejected_doc_coordinates).writexml()
        
        """Update the document status"""
        self._update_document_status(taskid, "REJECTED", "Unidentified Document, 80% Redaction done")

        """Remove document from workspace"""
        self._remove_document_from_workspace(document_path)

    def _remove_document_from_workspace(self, document_path):
        path = Path(document_path)
        path.unlink()
    
    def _webhook_post_request(self, taskid) -> bool:
        webhook_handler = WebhookHandler(self.db_client, taskid)
        return webhook_handler.post_request()
        # try:
        #     database_name = "upload"
        #     collection_name = "fileDetails"
        #     database = self.db_client[database_name]
        #     collection = database[collection_name]

        #     taskid_to_filter = {"taskId": taskid}
        #     result = collection.find_one(taskid_to_filter)

        #     if not result:
        #         self.logger.error(f"| No document found for task ID: {taskid}")
        #         return
            
        #     client_id = result['clientId']
        #     payload = {
        #         "taskId": result['taskId'],
        #         "status": result["status"],
        #         "taskResult": result["taskResult"],
        #         "clientId": result["clientId"],
        #         "uploadDir": result["uploadDir"]
        #     }

        #     """Get Client Webhook URL from webhook DB"""
        #     collection_name = "webhooks"
        #     database = self.db_client[database_name]
        #     collection = database[collection_name]
        #     filter_query = {"clientId": client_id}
        #     client_doc = collection.find_one(filter_query)
        #     if client_doc:
        #         WEBHOOK_URL = client_doc["url"]
        #         HEADER = {'Content-Type': 'application/json'}
        #         response = requests.post(WEBHOOK_URL+"/CVCore/processstatus", data=json.dumps(payload), headers=HEADER)
        #         if response.status_code != 200:
        #             self.logger.error(f"| Connecting to WebHOOK: {response.status_code}")
        #     else:
        #         self.logger.error(f"| Webhook URL not found for client ID: {client_id}")
        # except Exception as e:
        #     self.logger.error(f"| Webhook POST request: {e}")
        #     sys.exit(1)
