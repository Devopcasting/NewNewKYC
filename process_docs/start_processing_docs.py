import os
import sys
import shutil
import cv2
from time import sleep
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from perform_ocrr.ocrr_documents import PerformOCRROnDocuments

class ProcessDocuments:
    def __init__(self, in_progress_status_doc_q: object, doc_upload_path: str, workspace_path: str) -> None:
        self.in_progress_status_doc_q = in_progress_status_doc_q
        self.doc_upload_path = doc_upload_path
        self.workspace_path = workspace_path
        self.logger = OCRREngineLogging().configure_logger()
    
    def process_docs(self):
        while True:
            try:
                document_info = self.in_progress_status_doc_q.get()
                if document_info:
                    self._process_document(document_info)
                sleep(5)
            except Exception as e:
                self.logger.error(f"| Processing document: {str(e)}")

    def _process_document(self, document_info):
        self.logger.info(f"| Pre-Processing document {document_info['path']}")
        document_name_prefix = self._get_prefix_name(document_info['path'])
        document_name = os.path.basename(document_info['path'])
        renamed_doc_name = f"{document_name_prefix}{document_name}"
        jpeg_path = os.path.join(self.workspace_path, renamed_doc_name)

        """Copy the document to workspace"""
        shutil.copy(document_info['path'], jpeg_path)
        if not self._check_grayscale_document(jpeg_path):
            self._pre_process_document(jpeg_path)
        """Perform OCR and Redaction"""    
        self._perform_ocr_redaction(document_info, jpeg_path)
    
    def _pre_process_document(self, jpeg_path: str) -> bool:
        try:
            sigma_x = 1
            sigma_y = 1
            sig_alpha = 1.5
            sig_beta = -0.2
            gamma = 0
        
            document = cv2.imread(jpeg_path)
            denoise_document = cv2.fastNlMeansDenoisingColored(document, None, 10, 10, 7, 21)
            gray_document = cv2.cvtColor(denoise_document, cv2.COLOR_BGR2GRAY)
            gaussian_blur_document = cv2.GaussianBlur(gray_document, (5, 5), sigmaX=sigma_x, sigmaY=sigma_y)
            sharpened_image = cv2.addWeighted(gray_document, sig_alpha, gaussian_blur_document, sig_beta, gamma)
            sharpened_image_gray = cv2.cvtColor(sharpened_image, cv2.COLOR_GRAY2BGR)
            cv2.imwrite(jpeg_path, sharpened_image_gray)
            return True
        except Exception as e:
            self.logger.error(f"| Pre Processing Document {jpeg_path}: {e}")
            return False

    def _check_grayscale_document(self, jpeg_path: str) -> bool:
        document = cv2.imread(jpeg_path)
        if len(document.shape) < 3: return True
        if document.shape[2]  == 1: return True
        b,g,r = document[:,:,0], document[:,:,1], document[:,:,2]
        if (b==g).all() and (b==r).all(): return True
        return False

    def _perform_ocr_redaction(self, document_info, jpeg_path):
        room_name, room_id = document_info['path'].split("\\")[-3:-1]
        redacted_path = os.path.join(self.doc_upload_path, room_name, room_id, "Redacted")
        rejected_path = os.path.join(self.doc_upload_path, room_name, room_id, "Rejected")
        document_info_dict = {
            "taskId": document_info['taskId'],
            "roomName": room_name,
            "roomID": room_id,
            "documentName": document_info['path'].split("\\")[-1],
            "documentPath": jpeg_path,
            "uploadPath": self.doc_upload_path,
            "rejectedPath": rejected_path,
            "redactedPath": redacted_path
        }
        PerformOCRROnDocuments(document_info_dict).start_ocrr()

    def _get_prefix_name(self, document_path: str) -> str:
        room_name, room_id = document_path.split("\\")[-3:-1]
        return f"{room_name}+{room_id}+"