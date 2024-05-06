import re
import cv2
import configparser
import pytesseract
from qreader import QReader
from helper.extract_text_coordinates import TextCoordinates
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from documents.pancard.pattern_1 import PancardPattern1
from documents.pancard.pattern_2 import PancardPattern2

class PancardDocumentInfo:
    def __init__(self, document_path: str) -> None:
        self.document_path = document_path
        self._load_configuration()
        self._setup_logging()
        self._extract_text_coordinates()
        self.qreader = QReader()

    def _load_configuration(self):
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(r'C:\Program Files (x86)\OCRR\config\configuration.ini')
        self.DOCUMENT_REDACTION_LEVEL = int(config['Level']['RedactionLevel'])

    def _setup_logging(self):
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()
    
    def _extract_text_coordinates(self):
        self.coordinates = TextCoordinates(self.document_path, lang_type=None).generate_text_coordinates()
        self.coordinates_try1 = TextCoordinates(self.document_path, lang_type="dllang").generate_text_coordinates()
        tesseract_config = r'--oem 3 --psm 11'
        self.text_data = pytesseract.image_to_string(self.document_path, lang="eng", config=tesseract_config)
    
    def _extract_pancard_number(self):
        result = {
            "Pancard Number": "",
            "coordinates": []
        }
        try:
            pancard_number_text = ""
            pancard_number_coordinates = []
            pancard_coordinates = []
            matching_text_index = None
            matching_text_regex = r"\b(?:permanent|petmancnt|pe@fanent|pe@ffignent|pertianent|pereierent|account|number|card|perenent|accoun|pormanent|petraancnt)\b"
            contains_digit_and_alpha = lambda s: any(char.isdigit() for char in s) and any(char.isalpha() for char in s)

            """Find matching text regex and its index"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if re.search(matching_text_regex, text.lower(), flags=re.IGNORECASE):
                    matching_text_index = i
                    break

            if matching_text_index is None:
                search_range = range(len(self.coordinates))
            else:
                search_range = range(matching_text_index, len(self.coordinates))

            """Get the coordinates of pancard cards"""
            for i in search_range:
                text = self.coordinates[i][4]
                if len(text) in (7, 9, 10) and text.isupper() and contains_digit_and_alpha(text):
                    pancard_number_text += " " + text
                    pancard_number_coordinates.append([self.coordinates[i][0], self.coordinates[i][1], self.coordinates[i][2], self.coordinates[i][3]])
                elif len(text) in (7, 9, 10) and contains_digit_and_alpha(text):
                    pancard_number_text += " " + text
                    pancard_number_coordinates.append([self.coordinates[i][0], self.coordinates[i][1], self.coordinates[i][2], self.coordinates[i][3]])

            if not pancard_number_coordinates:
                """Try with other coordinates"""
                for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates_try1):
                    if len(text) in (7, 9, 10) and text.isupper() and contains_digit_and_alpha(text):
                        pancard_number_text += " "+ text
                        pancard_number_coordinates.append([self.coordinates_try1[i][0], self.coordinates_try1[i][1], self.coordinates_try1[i][2], self.coordinates_try1[i][3]])
                    elif len(text) in (7, 9, 10) and contains_digit_and_alpha(text):
                        pancard_number_text += " "+ text
                        pancard_number_coordinates.append([self.coordinates_try1[i][0], self.coordinates_try1[i][1], self.coordinates_try1[i][2], self.coordinates_try1[i][3]])
                if not pancard_number_coordinates:
                    return result
               
            """Get the final coordinates"""
            for i in pancard_number_coordinates:
                width = i[2] - i[0]
                pancard_coordinates.append([i[0], i[1], i[0] + int(0.65 * width),i[3]])

            result = {
                "Pancard Number": pancard_number_text,
                "coordinates": pancard_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"| Pancard Number: {e}")
            return result
        
    def _extract_dob(self):
        result = {
            "Pancard DOB": "",
            "coordinates": []
        }
        try:
            pancard_dob_text = ""
            pancard_dob_coordinates = []
            dob_coords = []

            date_pattern = r'\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}'
            for i, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
                match = re.search(date_pattern, text)
                if match:
                    pancard_dob_text += " "+ text
                    dob_coords.append([x1, y1, x2, y2])
            if not dob_coords:
                year_pattern = r'\b\d{4}\b'
                """Try if the string contains valid year pattern"""
                for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                    if re.search(year_pattern, text):
                        pancard_dob_text += " "+ text
                        dob_coords.append([x1, y1, x2, y2])
                        break
                if not dob_coords:
                    return result
            
            """Get the coordinates"""
            for i in dob_coords:
                width = i[2] - i[0]
                pancard_dob_coordinates.append([i[0], i[1], i[0] + int(0.54 * width), i[3]])
            result = {
                "Pancard DOB": pancard_dob_text,
                "coordinates": pancard_dob_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"| Pancard DOB: {e}")
            return result

    def _extract_qrcode(self):
        result = {
            "Pancard QR Code": "",
            "coordinates": []
            }
        try:
            qrcode_coordinates = []

            """Load the image"""
            image = cv2.imread(self.document_path)

            """Detect and decode QR codes"""
            found_qrs = self.qreader.detect(image)

            if not found_qrs:
                return result
            
            """get 50% of QR Code"""
            for i in found_qrs:
                x1, y1, x2, y2 = i['bbox_xyxy']
                qrcode_coordinates.append([int(round(x1)), int(round(y1)), int(round(x2)), (int(round(y1)) + int(round(y2))) // 2])
                #qrcode_coordinates.append([int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))])
        
            result = {
                "Pancard QR-Code": f"Found {len(qrcode_coordinates)} QR Codes",
                "coordinates": qrcode_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"| Pancard QR-Code: {e}")
            return result
        
    def _extract_signature(self):
        result = {
            "Pancard Signature": "",
            "coordinates": []
        }
        try:
            matching_text_keyword = ["signature", "nature", "asignature","/signature","(signature", "sehat", "signatite"]
            pancard_signature_coordinates = []
            pattern = self._identify_pancard_patterns()

            if pattern == 1:
                """Get the coordinates"""
                for i,(x1,y1,x2,y2,text) in enumerate(self.coordinates):
                    if text.lower() in matching_text_keyword:
                        pancard_signature_coordinates = [[self.coordinates[i + 1][0], self.coordinates[i + 1][1], self.coordinates[i + 1][2], self.coordinates[i + 1][3]]]
                        break
            else:
                for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                    if text.lower() in matching_text_keyword:
                        pancard_signature_coordinates.append([self.coordinates[i - 2][0], self.coordinates[i - 2][1], self.coordinates[i - 2][2], self.coordinates[i - 2][3]])
                        break

            if not pancard_signature_coordinates:
                return result
            
            result = {
                    "Pancard Signature": "User Signature",
                    "coordinates": pancard_signature_coordinates
                }
            return result
        except Exception as e:
            self.logger.error(f"| Pancard Signature: {e}")
            return result

    def _identify_pancard_patterns(self) -> int:
        pancard_pattern_keyword_search = ["father's name", "father", "/eather's", "father's", 
                                          "ffatubr's", "fathers", "hratlieies", "ffatugr's",
                                          "/father s name", "father s name", "/father's", "facer","race", "eaters"]
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if text.lower() in pancard_pattern_keyword_search:
                return 1
        return 2

    def collect_pancard_document_info(self):
        pancard_doc_info_list = []
        pattern = self._identify_pancard_patterns()

        try:
            """Get the redaction level"""

            if self.DOCUMENT_REDACTION_LEVEL == 1:
                """REDACTION LEVEL : 1"""

                """Collect: Pancard Number Coordinates"""
                pancard_number = self._extract_pancard_number()
                pancard_number_status = False
                if len(pancard_number['coordinates']) != 0:
                    pancard_number_status = True
                pancard_doc_info_list.append(pancard_number)

                """Collect: Pancard DOB"""
                pancard_dob = self._extract_dob()
                pancard_dob_status = False
                if len(pancard_dob['coordinates']) != 0:
                    pancard_dob_status = True
                pancard_doc_info_list.append(pancard_dob)

                """Collect: Pancard User and Father's names"""        
                if pattern == 1:
                    """Username"""
                    matching_text_keyword_username = ["ann","flame","name", "uiname","aname", "nin", "mame", "ssapcassh"]
                    username_p1 = PancardPattern1(self.coordinates, self.text_data, matching_text_keyword_username, "User").extract_user_father_name()
                    username_p1_status = False
                    if len(username_p1['coordinates']) != 0:
                        username_p1_status = True
                    pancard_doc_info_list.append(username_p1)

                    """Father's Name"""
                    matching_text_keyword_fathername = ["father's name", "father", "/eather's", "father's", 
                                          "ffatubr's", "fathers", "hratlieies", "ffatugr's",
                                          "/father s name", "father s name", "/father's", "facer","race", "eaters"]
                    fathers_name_p1 = PancardPattern1(self.coordinates, self.text_data, matching_text_keyword_fathername, "Father").extract_user_father_name()
                    fathers_name_p1_status = True
                    if len(fathers_name_p1['coordinates']) != 0:
                        fathers_name_p1_status = True
                    pancard_doc_info_list.append(fathers_name_p1)
                else:
                    """Username"""
                    username_p2 = PancardPattern2(self.coordinates, self.text_data, "User").extract_username_p2()
                    username_p2_status = False
                    if len(username_p2['coordinates']) != 0:
                        username_p2_status = True
                    pancard_doc_info_list.append(username_p2)

                    """Father's Name"""
                    fathername_p2 = PancardPattern2(self.coordinates, self.text_data, "Father").extract_father_name_p2()
                    fathername_p2_status = False
                    if len(fathername_p2['coordinates']) != 0:
                        fathername_p2_status = True
                    pancard_doc_info_list.append(fathername_p2)
                
                """Collect: QR-Codes"""
                qrcode = self._extract_qrcode()
                qrcode_status = False
                if len(qrcode['coordinates']) != 0:
                    qrcode_status = True
                pancard_doc_info_list.append(qrcode)

                """Collect: Signature"""
                pancard_signature = self._extract_signature()
                pancard_signature_status = False
                if len(pancard_signature['coordinates']) != 0:
                    pancard_signature_status = True
                pancard_doc_info_list.append(pancard_signature)

                """If Pancard number, username and fathername and DOB is not available then reject the document."""
                if pattern == 1:
                    status = [pancard_number_status, pancard_dob_status, username_p1_status, fathers_name_p1_status ]
                    all_false = all(not var_status for var_status in status)
                else:
                    status = [pancard_number_status, pancard_dob_status, username_p2_status, fathername_p2_status ]
                    all_false = all(not var_status for var_status in status)
                
                if all_false:
                    self.logger.error(f"| Complete Pancard document information not available")
                    return {"message": "Unable to extract Pancard information", "status": "REJECTED"}

                """Check if all the dictionaries in the list are empty"""
                all_keys_and_coordinates_empty =  all(all(not v for v in d.values()) for d in pancard_doc_info_list)
                if all_keys_and_coordinates_empty:
                    self.logger.error(f"| Unable to extract Pancard document information")
                    return {"message": "Unable to extract Pancard document information", "status": "REJECTED"}
                else:
                    self.logger.info(f"| Successfully Redacted Pancard Document")
                    return {"message": "Successfully Redacted Pancard Document", "status": "REDACTED", "data": pancard_doc_info_list}
            else:
                """REDACTION LEVEL : 2"""
                
                """Collect: Pancard Number Coordinates"""
                pancard_number = self._extract_pancard_number()
                if len(pancard_number['coordinates']) == 0:
                    self.logger.error(f"| Unable to extract Pancard Number")
                    return {"message": "Unable to extract Pancard Number", "status": "REJECTED"}
                pancard_doc_info_list.append(pancard_number)

                """Collect: Pancard DOB"""
                pancard_dob = self._extract_dob()
                if len(pancard_dob['coordinates']) == 0:
                    self.logger.error(f"| Unable to extract Pancard DOB")
                    return {"message": "Unable to extract Pancard DOB", "status": "REJECTED"}
                pancard_doc_info_list.append(pancard_dob)

                """Collect: Pancard User and Father's names"""        
                if pattern == 1:
                    """Username"""
                    matching_text_keyword_username = ["name", "uiname","aname", "nin", "mame", "ssapcassh"]
                    username_p1 = PancardPattern1(self.coordinates, self.text_data, matching_text_keyword_username, "User").extract_user_father_name()
        
                    if len(username_p1['coordinates']) == 0:
                        self.logger.error(f"| Unable to extract Pancard Username")
                        return {"message": "Unable to extract Pancard Username", "status": "REJECTED"}
                    pancard_doc_info_list.append(username_p1)

                    """Father's Name"""
                    matching_text_keyword_fathername = ["father's name", "father", "/eather's", "father's", 
                                          "ffatubr's", "fathers", "hratlieies", "ffatugr's",
                                          "/father s name", "father s name", "/father's", "facer","race"]
                    fathers_name_p1 = PancardPattern1(self.coordinates, self.text_data, matching_text_keyword_fathername, "Father").extract_user_father_name()
                    
                    if len(fathers_name_p1['coordinates']) == 0:
                        self.logger.error(f"| Unable to extract Pancard Father's name")
                        return {"message": "Unable to extract Pancard Father's name", "status": "REJECTED"}
                    pancard_doc_info_list.append(fathers_name_p1) 
                else:
                    """Username"""
                    username_p2 = PancardPattern2(self.coordinates, self.text_data, "User").extract_username_p2()
                    if len(username_p2['coordinates']) == 0:
                        self.logger.error(f"| Unable to extract Pancard Username")
                        return {"message": "Unable to extract Pancard Username", "status": "REJECTED"}
                    pancard_doc_info_list.append(username_p2)

                    """Father's Name"""
                    fathername_p2 = PancardPattern2(self.coordinates, self.text_data, "Father").extract_father_name_p2()
                    if len(fathername_p2['coordinates']) != 0:
                        self.logger.error(f"| Unable to extract Pancard Father's name")
                        return {"message": "Unable to extract Pancard Father's name", "status": "REJECTED"}
                    pancard_doc_info_list.append(fathername_p2)
                
                """Collect: QR-Codes"""
                qrcode = self._extract_qrcode()
                if len(qrcode['coordinates']) == 0:
                    self.logger.error(f"| Unable to extract QR-Code from Pancard")
                pancard_doc_info_list.append(qrcode)

                """Collect: Signature"""
                pancard_signature = self._extract_signature()
                if len(pancard_signature['coordinates']) == 0:
                    self.logger.error(f"| Unable to extract Signature from Pancard")
                pancard_doc_info_list.append(pancard_signature)

                self.logger.info(f"| Successfully Redacted Pancard Document")
                return {"message": "Successfully Redacted Pancard Document", "status": "REDACTED", "data": pancard_doc_info_list}
        except Exception as e:
            self.logger.error(f"| Collecting Pancard document information: {e}")
            return {"message": "Error collecting Pancard document information", "status": "REJECTED"}