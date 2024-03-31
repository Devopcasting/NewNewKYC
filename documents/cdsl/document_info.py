import configparser
import pytesseract
from helper.extract_text_coordinates import TextCoordinates
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging

class CDSLDocumentInfo:
    def __init__(self, document_path: str) -> None:
        self.document_path = document_path
        self._load_configuration()
        self._setup_logging()
        self._extract_text_coordinates()
    
    def _load_configuration(self):
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(r'C:\Program Files (x86)\OCRR\config\configuration.ini')
        self.DOCUMENT_REDACTION_LEVEL = int(config['Level']['RedactionLevel'])

    def _setup_logging(self):
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()
    
    def _extract_text_coordinates(self):
        self.coordinates = TextCoordinates(self.document_path, lang_type="default").generate_text_coordinates()
        self.text_data = pytesseract.image_to_string(self.document_path)

    def _extract_pancard_number(self) -> dict:
        result = {
            "CDSL Pancard Number": "",
            "coordinates": []
        }
        try:
            pancard_number_text = ""
            pancard_number_coordinates = []

            contains_digit_and_alpha = lambda s: any(char.isdigit() for char in s) and any(char.isalpha() for char in s)
            for x1, y1, x2, y2, text in self.coordinates:
                if len(text) == 10 and text.isupper() and contains_digit_and_alpha(text):
                    width = x2 - x1
                    pancard_number_coordinates = [x1, y1, x2, y2]
                    pancard_number_text = text
                    break
            if not pancard_number_coordinates:
                return result
            result = {
                "CDSL Pancard Number": pancard_number_text,
                "coordinates": [[
                        pancard_number_coordinates[0], 
                        pancard_number_coordinates[1],
                        pancard_number_coordinates[0] + int(0.65 * width),
                        pancard_number_coordinates[3]
                ]]
            }
            return result
        except Exception as e:
            self.logger.error(f"| CDL Pancard number: {e}")
            return result
    
    def _extract_username(self) -> dict:
        result = {
            "CDSL Username": "",
            "coordinates": []
        }
        try:
            username_text = ""
            username_coordinates = []
            pancard_number_index = None

            """Get the index of pancard number"""
            contains_digit_and_alpha = lambda s: any(char.isdigit() for char in s) and any(char.isalpha() for char in s)
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if len(text) == 10 and text.isupper() and contains_digit_and_alpha(text):
                    pancard_number_index = i
                    break
            if pancard_number_index is None:
                return result
            
            """Get the coordinates"""
            for i in range(pancard_number_index +1 , len(self.coordinates)):
                text = self.coordinates[i][4]
                if text.lower() in ["current", "kin", "ikyc", "kyc", "kra", "kyo", "date"]:
                    break
                if text.isupper() and text.isalpha():
                    username_text += " "+ text
                    username_coordinates.append([self.coordinates[i][0], self.coordinates[i][1],
                                                 self.coordinates[i][2], self.coordinates[i][3]])
                elif text.lower() in ["name", ":"]:
                    continue
                elif text[0].isupper() and text[1:].islower():
                    username_text += " "+ text
                    username_coordinates.append([self.coordinates[i][0], self.coordinates[i][1],
                                                 self.coordinates[i][2], self.coordinates[i][3]])
            
            if len(username_coordinates) > 1:
                result = {
                    "CDSL Username": username_text,
                    "coordinates": [[username_coordinates[0][0], username_coordinates[0][1], username_coordinates[-1][2], username_coordinates[-1][3]]]
                }
            else:
                result = {
                    "CDSL Username": username_text,
                    "coordinates": [[username_coordinates[0][0], username_coordinates[0][1], username_coordinates[0][2], username_coordinates[0][3]]]
                }
            return result
        except Exception as e:
            self.logger.error(f"| CDSL Username: {e}")
            return result

    def collect_cdsl_document_info(self):
        cdsl_doc_info_list = []
        try:
            """Get the redaction level"""
            if self.DOCUMENT_REDACTION_LEVEL == 1:
                """Collect: Pancard Number Coordinates"""
                cdsl_doc_info_list.append(self._extract_pancard_number())

                """Collect: Username"""
                cdsl_doc_info_list.append(self._extract_username())

                """Check if all the dictionaries in the list are empty"""
                all_keys_and_coordinates_empty =  all(all(not v for v in d.values()) for d in cdsl_doc_info_list)
                if all_keys_and_coordinates_empty:
                    return {"message": "Unable to extract CDSL document information", "status": "REJECTED"}
                else:
                    return {"message": "Successfully Redacted CDSL Document", "status": "REDACTED", "data": cdsl_doc_info_list}
            else:
                """Collect: Pancard Number Coordinates"""
                pancard_number = self._extract_pancard_number()
                if len(pancard_number['coordinates']) == 0:
                    self.logger.error(f"| Unable to extract Pancard Number from CDSL")
                    return {"message": "Unable to extract Pancard Number from CDSL", "status": "REJECTED"}
                cdsl_doc_info_list.append()

                """Collect: Username"""
                username = self._extract_username()
                if len(username['coordinates']) == 0:
                    self.logger.error(f"| Unable to extract Username from CDSL")
                    return {"message": "Unable to extract Username from CDSL", "status": "REJECTED"}
                cdsl_doc_info_list.append()

                return {"message": "Successfully Redacted CDSL Document", "status": "REDACTED", "data": cdsl_doc_info_list}

        except Exception as e:
            self.logger.error(f"| Collecting CDSL document information: {e}")
            return {"message": "Error collecting CDSL document information", "status": "REJECTED"}
