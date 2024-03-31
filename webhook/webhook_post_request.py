import requests
import json
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging

class WebhookHandler:
    def __init__(self, db_client, taskid) -> None:
        self.db_client = db_client
        self.taskid = taskid
        self.logger = OCRREngineLogging().configure_logger()
    
    def post_request(self) -> bool:
        try:
            database_name = "upload"
            collection_name = "fileDetails"
            database = self.db_client[database_name]
            collection = database[collection_name]

            taskid_to_filter = {"taskId": self.taskid}
            result = collection.find_one(taskid_to_filter)

            if not result:
                self.logger.error(f"| No document found for task ID: {self.taskid}")
                return
            
            client_id = result['clientId']
            payload = {
                "taskId": result['taskId'],
                "status": result["status"],
                "taskResult": result["taskResult"],
                "clientId": result["clientId"],
                "uploadDir": result["uploadDir"]
            }

            """Get Client Webhook URL from webhook DB"""
            collection_name = "webhooks"
            database = self.db_client[database_name]
            collection = database[collection_name]
            filter_query = {"clientId": client_id}
            client_doc = collection.find_one(filter_query)
            if client_doc:
                WEBHOOK_URL = client_doc["url"]
                HEADER = {'Content-Type': 'application/json'}
                response = requests.post(WEBHOOK_URL+"/CVCore/processstatus", data=json.dumps(payload), headers=HEADER)
                if response.status_code != 200:
                    self.logger.error(f"| Connecting to WebHOOK: {response.status_code}")
                    return False
            else:
                self.logger.error(f"| Webhook URL not found for client ID: {client_id}")
                return False
        except Exception as e:
            self.logger.error(f"| Webhook POST request: {e}")
            return False