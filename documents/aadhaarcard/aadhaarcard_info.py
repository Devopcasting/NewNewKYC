import re
import cv2
import datetime
import configparser
import pytesseract
from qreader import QReader
from helper.extract_text_coordinates import TextCoordinates
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from config.indian_places import indian_states_cities

class AadhaarCardDocumentInfo:
    def __init__(self, document_path: str) -> None:
        self.document_path = document_path
        self._load_configuration()
        self._setup_logging()
        self._extract_text_coordinates()
        self.qreader = QReader()
        self.states = indian_states_cities

    def _load_configuration(self):
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(r'C:\Program Files (x86)\OCRR\config\configuration.ini')
        self.DOCUMENT_REDACTION_LEVEL = int(config['Level']['RedactionLevel'])

    def _setup_logging(self):
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()
    
    def _extract_text_coordinates(self):
        self.coordinates_default = TextCoordinates(self.document_path, lang_type="default").generate_text_coordinates()
        self.coordinates_regional = TextCoordinates(self.document_path, lang_type="regional").generate_text_coordinates()
        #print(self.coordinates_default
        self.text_data_default = pytesseract.image_to_string(self.document_path)
        tesseract_config = r'--oem 3 --psm 11'
        self.text_data_regional = pytesseract.image_to_string(self.document_path, lang="hin+eng", config=tesseract_config)
        #print(self.text_data)
    
    def _extract_dob(self):
        result = {
            "Aadhaar DOB": "",
            "coordinates": []
            }
        try:
            dob_text = ""
            dob_coordinates = []
        
            """Data patterns: DD/MM/YYY, DD-MM-YYY"""
            date_pattern = r'\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}|\d{4}'

            for i, (x1, y1, x2, y2, text) in enumerate(self.coordinates_default):
                match = re.search(date_pattern, text)
                if match:
                    dob_coordinates = [x1, y1, x2, y2]
                    dob_text = text
                    break
        
            if not dob_coordinates:
                return result
        
            """Get first 6 chars"""
            width = dob_coordinates[2] - dob_coordinates[0]
            result = {
                "Aadhaar DOB": dob_text,
                "coordinates": [[dob_coordinates[0], dob_coordinates[1], dob_coordinates[0] + int(0.54 * width), dob_coordinates[3]]]
            }
            return result
        except Exception as e:
            self.logger.error(f"| Aadhaar DOB: {e}")
            return result
    
    def collect_aadhaarcard_info(self):
        aadhaarcard_doc_info_list = []

        try:
            """Get the redaction level"""
            if self.DOCUMENT_REDACTION_LEVEL == 1:

                """Collect DOB"""
                dob = self._extract_dob()
                aadhaarcard_doc_info_list.append(dob)

                """Check if all the dictionaries in the list are empty"""
                all_keys_and_coordinates_empty =  all(all(not v for v in d.values()) for d in aadhaarcard_doc_info_list)
                if all_keys_and_coordinates_empty:
                    self.logger.error(f"| Unable to extract Aadhaar document information")
                    return {"message": "Unable to extract Aadhaar document information", "status": "REJECTED"}
                else:
                    self.logger.info(f"| Successfully Redacted Aadhaar Document")
                    return {"message": "Successfully Redacted Aadhaar Document", "status": "REDACTED", "data": aadhaarcard_doc_info_list}
            else:
                pass
        except Exception as e:
            self.logger.error(f"| Collecting Aadhaar document information: {e}")
            return {"message": "Error collecting Aadhaar document information", "status": "REJECTED"}
