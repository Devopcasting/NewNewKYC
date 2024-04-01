import re
import cv2
import configparser
import pytesseract
from PIL import Image
from qreader import QReader
from helper.extract_text_coordinates import TextCoordinates
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging

class EPancardDocumentInfo:
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
        #print(self.coordinates)
        tesseract_config = r'--oem 3 --psm 11'
        self.text_data = pytesseract.image_to_string(self.document_path, lang="eng", config=tesseract_config)
        #print(self.text_data)

    def _extract_pancard_number(self) -> dict:
        result = {
            "E-Pancard Number": "",
            "coordinates": []
            }
        try:
            pancard_text = ""
            pancard_coordinates = []
        
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if len(text) == 10 and text.isupper() and text.isalnum() and any(char.isdigit() for char in text):
                    pancard_coordinates.append([x1, y1, x2, y2])
                    pancard_text = text
        
            if not pancard_coordinates:
                return result
        
            width = pancard_coordinates[0][2] - pancard_coordinates[0][0]
            result = {
                "E-Pancard Number": pancard_text,
                "coordinates": [[pancard_coordinates[0][0], pancard_coordinates[0][1], 
                       pancard_coordinates[0][0] + int(0.65 * width),pancard_coordinates[0][3]]]
            }
            return result
        except Exception as e:
            self.logger.error(f"| E-Pancard Number: {e}")
            return result

    def _extract_dob(self):
        result = {
            "E-Pancard DOB": "",
            "coordinates": []
            }
        try:
            dob_text = ""
            dob_coordinates = []

            """Data patterns: DD/MM/YYY, DD-MM-YYY"""
            date_pattern = r'\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}'

            for i, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
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
                "E-Pancard DOB": dob_text,
                "coordinates": [[dob_coordinates[0], dob_coordinates[1], dob_coordinates[0] + int(0.54 * width), dob_coordinates[3]]]
            }
            return result
        except Exception as e:
            self.logger.error(f"| E-Pancard DOB: {e}")
            return result
    
    def _extract_gender(self):
        result = {
            "E-Pancard Gender": "",
            "coordinates": []
            }
        try:
            gender_text = ""
            gender_coordinates = []

            gender_pattern = r"male|female"
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if re.search(gender_pattern, text, flags=re.IGNORECASE):
                    gender_coordinates.append([x1, y1, x2, y2])
                    gender_text = text
                    break
            if not gender_coordinates:
                return result
            
            result = {
                "E-Pancard Gender": gender_text,
                "coordinates": gender_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"| E-Pancard Gender: {e}")
            return result
        
    def _extract_name(self):
        result = {
            "E-Pancard Name": "",
            "coordinates": []
            }
        try:
            name_text = ""
            name_coordinates = []
            matching_name_list = []

            clean_text = [i for i in self.text_data.split("\n") if len(i) != 0]
            for i,text in enumerate(clean_text):
                if 'ata /Name' in text:
                    matching_name_list = clean_text[i + 1].split()
                    name_text = clean_text[i + 1]
                    break
        
            if not matching_name_list:
                return result
        
            if len(matching_name_list) > 1:
                matching_name_list = matching_name_list[:-1]

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if text in matching_name_list:
                    name_coordinates.append([x1, y1, x2, y2])
                if len(matching_name_list) == len(name_coordinates):
                    break
        
            if len(name_coordinates) > 1:
                result = {
                    "E-Pancard Name": name_text,
                    "coordinates": [[name_coordinates[0][0], name_coordinates[0][1], name_coordinates[-1][2], name_coordinates[-1][3]]]
                }
            else:
                result = {
                    "E-Pancard Name": name_text,
                    "coordinates": [[name_coordinates[0][0], name_coordinates[0][1], name_coordinates[0][2], name_coordinates[0][3]]]
                }
            return result
        except Exception as e:
            self.logger.error(f"| E-Pancard Name: {e}")
            return result

    def _extract_father_name(self):
        result = {
            "E-Pancard Father's Name": "",
            "coordinates": []
            }
        try:
            father_name_text = ""
            father_name_coordinates = []
            matching_name_list = []

            clean_text = [i for i in self.text_data.split("\n") if len(i) != 0]
            for i,text in enumerate(clean_text):
                if 'Father' in text:
                    matching_name_list = clean_text[i + 1].split()
                    father_name_text = clean_text[i + 1]
                    break
        
            if not matching_name_list:
                return result
        
            if len(matching_name_list) > 1:
                matching_name_list = matching_name_list[:-1]

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if text in matching_name_list:
                    father_name_coordinates.append([x1, y1, x2, y2])
                if len(matching_name_list) == len(father_name_coordinates):
                    break
        
            if len(father_name_coordinates) > 1:
                result = {
                    "E-Pancard Father's Name": father_name_text,
                    "coordinates": [[father_name_coordinates[0][0], father_name_coordinates[0][1], father_name_coordinates[-1][2], father_name_coordinates[-1][3]]]
                }
            else:
                result = {
                    "E-Pancard Father's Name": father_name_text,
                    "coordinates": [[father_name_coordinates[0][0], father_name_coordinates[0][1], father_name_coordinates[0][2], father_name_coordinates[0][3]]]
                }
            return result
        except Exception as e:
            self.logger.error(f"| E-Pancard Father's Name: {e}")
            return result

    """func: redact bottom pancard"""
    def _redact_bottom_pancard(self):
        result = {}
        bottom_coordinates = []
        image = Image.open(self.document_path)
        image_width, image_height = image.size
        bottom_coordinates.append(self.bottom_40_percent_coordinates(image_width, image_height))

        result = {
            "E-Pancard": "E-Pancard",
            "coordinates": bottom_coordinates
        }
        return result
    
    def bottom_40_percent_coordinates(self, image_width, image_height) -> list:
        x1 = 0
        y1 = int(0.8 * image_height)  # 60% from the top is 40% from the bottom
        x2 = image_width // 2
        y2 = image_height
        return [x1, y1, x2, y2]

    def _extract_qr_code(self):
        result = {
            "E-Pancard QR Code": "",
            "coordinates": []
            }
        try:
            qrcode_coordinates = []
            # Load the image
            image = cv2.imread(self.document_path)

            # Detect and decode QR codes
            found_qrs = self.qreader.detect(image)

            if not found_qrs:
                return result
        
            """get 50% of QR Code"""
            for i in found_qrs:
                x1, y1, x2, y2 = i['bbox_xyxy']
                qrcode_coordinates.append([int(round(x1)), int(round(y1)), int(round(x2)), (int(round(y1)) + int(round(y2))) // 2])
                #qrcode_coordinates.append([int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))])
        
            result = {
                "E-Pancard QR Code": f"Found {len(qrcode_coordinates)} QR Codes",
                "coordinates": qrcode_coordinates
            }
            return result
        except Exception as error:
            self.logger.error(f"Error: E-Pancard QR Code | {error}")
            return result
    
    def collect_e_pancard_document_info(self):
        e_pancard_doc_info_list = []
        try:
            if self.DOCUMENT_REDACTION_LEVEL == 1:

                """Collect Pancard number"""
                pancard_number = self._extract_pancard_number()
                e_pancard_doc_info_list.append(pancard_number)

                """Collect DOB"""
                dob = self._extract_dob()
                e_pancard_doc_info_list.append(dob)

                """Collect Gender"""
                gender = self._extract_gender()
                e_pancard_doc_info_list.append(gender)

                """Collect Name"""
                username = self._extract_name()
                e_pancard_doc_info_list.append(username)

                """Collect Father's name"""
                father_name = self._extract_father_name()
                e_pancard_doc_info_list.append(father_name)

                """Collect QR-Code"""
                qrcode = self._extract_qr_code()
                e_pancard_doc_info_list.append(qrcode)

                """Collect Bottom Pancard"""
                bottom_pan = self._redact_bottom_pancard()
                e_pancard_doc_info_list.append(bottom_pan)

                """Check if all the dictionaries in the list are empty"""
                all_keys_and_coordinates_empty =  all(all(not v for v in d.values()) for d in e_pancard_doc_info_list)
                if all_keys_and_coordinates_empty:
                    self.logger.error(f"| Unable to extract E-Pancard document information")
                    return {"message": "Unable to extract E-Pancard document information", "status": "REJECTED"}
                else:
                    self.logger.info(f"| Successfully Redacted E-Pancard Document")
                    return {"message": "Successfully Redacted E-Pancard Document", "status": "REDACTED", "data":e_pancard_doc_info_list}
            else:

                """Collect Pancard number"""
                pancard_number = self._extract_pancard_number()
                if len(pancard_number['coordinates']) == 0:
                    self.logger.error(f"| Unable to extract E-Pancard Number not found")
                    return {"message": "Unable to extract E-Pancard Number not found", "status": "REJECTED"}
                e_pancard_doc_info_list.append(pancard_number)

                """Collect DOB"""
                dob = self._extract_dob()
                if len(dob['coordinates']) == 0:
                    self.logger.error(f"| Unable to extract E-Pancard DOB not found")
                    return {"message": "Unable to extract E-Pancard DOB not found", "status": "REJECTED"}
                e_pancard_doc_info_list.append(dob)

                """Collect Gender"""
                gender = self._extract_gender()
                if len(gender['coordinates']) == 0:
                    self.logger.error(f"| Unable to extract E-Pancard Gender not found")
                    return {"message": "Unable to extract E-Pancard Gender not found", "status": "REJECTED"}
                e_pancard_doc_info_list.append(gender)

                """Collect Name"""
                username = self._extract_name()
                if len(username['coordinates']) == 0:
                    self.logger.error(f"| Unable to extract E-Pancard Username not found")
                    return {"message": "Unable to extract E-Pancard Username not found", "status": "REJECTED"}
                e_pancard_doc_info_list.append(username)

                """Collect Father's name"""
                father_name = self._extract_father_name()
                if len(father_name['coordinates']) == 0:
                    self.logger.error(f"| Unable to extract E-Pancard Father's name not found")
                    return {"message": "Unable to extract E-Pancard Father's name not found", "status": "REJECTED"}
                e_pancard_doc_info_list.append(father_name)

                """Collect QR-Code"""
                qrcode = self._extract_qr_code()
                e_pancard_doc_info_list.append(qrcode)

                """Collect Bottom Pancard"""
                bottom_pan = self._redact_bottom_pancard()
                e_pancard_doc_info_list.append(bottom_pan)

                self.logger.info(f"| Successfully Redacted E-Pancard Document")
                return {"message": "Successfully Redacted E-Pancard Document", "status": "REDACTED", "data": e_pancard_doc_info_list}
        except Exception as e:
            self.logger.error(f"| Collecting E-Pancard document information: {e}")
            return {"message": "Error collecting E-Pancard document information", "status": "REJECTED"}
