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
        #print(self.coordinates_default)
        self.coordinates_regional = TextCoordinates(self.document_path, lang_type="regional").generate_text_coordinates()
        self.text_data_default = pytesseract.image_to_string(self.document_path)
        tesseract_config = r'--oem 3 --psm 11'
        self.text_data_regional = pytesseract.image_to_string(self.document_path, lang="hin+eng", config=tesseract_config)
        #print(self.coordinates_regional)
        print(self.text_data_regional)
    
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
    
    def _extract_gender(self):
        result = {
            "Aadhaar Gender": "",
            "coordinates": []
        }
        try:
            gender_text = ""
            gender_coordinates = []

            gender_pattern = r"male|female"
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates_default):
                if re.search(gender_pattern, text, flags=re.IGNORECASE):
                    gender_coordinates.append([x1, y1, x2, y2])
                    gender_text = text
                    break
            if not gender_coordinates:
                """Try getting the coordinates from coordinates_regional"""
                for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates_regional):
                    if re.search(gender_pattern, text, flags=re.IGNORECASE):
                        gender_text = text
                        gender_coordinates.append([self.coordinates_regional[i -1][0], self.coordinates_regional[i -1][1], x2, y2])
                        break
                if not gender_coordinates:
                    return result
            
            result = {
                "Aadhaar Gender": gender_text,
                "coordinates": gender_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"| Aadhaar Gender: {e}")
            return result

    def _extract_aadhaar_number(self):
        result = {
            "Aadhaar Number": "",
            "coordinates": []
            }
        try:
            aadhaarcard_text = ""
            aadhaarcard_coordinates = []
            text_coordinates = []
            UseRegionalCoords = False

            """get the index of male/female"""
            matching_index = None
            gender_pattern = r"male|female"
            for i,(x1,y1,x2,y2,text) in enumerate(self.coordinates_default):
                if re.search(gender_pattern, text, flags=re.IGNORECASE):
                    matching_index = i

            if matching_index is None:
                """Try getting the index from coordinates_regional"""
                for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates_regional):
                    if re.search(gender_pattern, text, flags=re.IGNORECASE):
                        matching_index = i
                        UseRegionalCoords = True
                if matching_index is None:
                    return result
        
            """get the coordinates of aadhaar card number"""
            if UseRegionalCoords:
                use_this_coords = self.coordinates_regional
            else:
                use_this_coords = self.coordinates_default

            for i in range(matching_index, len(use_this_coords)):
                text = self.coordinates_default[i][4]
                if len(text) == 4 and text.isdigit() and text[:2] != '19':
                    text_coordinates.append((text))
                    aadhaarcard_text += ' '+ text
                if len(text_coordinates) == 3:
                    break
        
            for i in text_coordinates[:-1]:
                for k,(x1,y1,x2,y2,text) in enumerate(self.coordinates_default):
                    if i in text:
                        aadhaarcard_coordinates.append([x1, y1, x2, y2])

            result = {
                "Aadhaar Number": aadhaarcard_text,
                "coordinates": aadhaarcard_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"| Aadhaar Number: {e}")
            return result

    def _extract_name_in_eng(self):
        result = {
            "Aadhaar Name in English": "",
            "coordinates": []
            }
        try:
            name_text = ""
            name_coordinates = []

            """split the text into lines"""
            lines = [i for i in self.text_data_default.splitlines() if len(i) != 0]
        
            """regex patterns"""
            dob_pattern = re.compile(r"DOB", re.IGNORECASE)
            date_pattern = re.compile(r"\d{1,2}/\d{1,2}/\d{4}")
            year_pattern = re.compile(r"\d{4}")

            """get the matching text index"""
            for i, item in enumerate(lines):
                if dob_pattern.search(item) or date_pattern.search(item) or year_pattern.search(item):
                    name_text = lines[i - 1]
                    break
            if not name_text:
                return result
        
            """split the name"""
            name_text_split = name_text.split()
            if len(name_text_split) > 1:
                name_text_split = name_text_split[:-1]
        
            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates_default):
                if text in name_text_split:
                    name_coordinates.append([x1, y1, x2, y2])
                if len(name_text_split) == len(name_coordinates):
                    break
        
            if len(name_text_split) > 1:
                result = {
                    "Aadhaar Name in English": name_text,
                    "coordinates": [[name_coordinates[0][0], name_coordinates[0][1], name_coordinates[-1][2], name_coordinates[-1][3]]]
                }
            else:
                result = {
                    "Aadhaar Name in English": name_text,
                    "coordinates": [[name_coordinates[0][0], name_coordinates[0][1], name_coordinates[0][2], name_coordinates[0][3]]]
            }
            return result
        except Exception as e:
            self.logger.error(f"| Aadhaar Name in English: {e}")
            return result
    
    def _extract_name_in_native(self):
        result = {
            "Aadhaar Name in Native": "",
            "coordinates": []
            }
        try:
            name_text = ""
            name_coordinates = []

            """split the text into lines"""
            lines = [i for i in self.text_data_regional.splitlines() if len(i) != 0]
    
            """get the matching text index"""
            gender_pattern = r"male|female"
            for i, item in enumerate(lines):
                if re.search(gender_pattern, item, flags=re.IGNORECASE):
                    name_text = lines[i - 4]
                    break
            if not name_text:
                return result
        
            """split the name"""
            name_text_split = name_text.split()
            if len(name_text_split) > 1:
                name_text_split = name_text_split[:-1]
        
            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates_regional):
                if text in name_text_split:
                    name_coordinates.append([x1, y1, x2, y2])
                if len(name_text_split) == len(name_coordinates):
                    break
        
            if len(name_text_split) > 1:
                result = {
                    "Aadhaar Name in Native": name_text,
                    "coordinates": [[name_coordinates[0][0], name_coordinates[0][1], name_coordinates[-1][2], name_coordinates[-1][3]]]
                }
            else:
                result = {
                    "Aadhaar Name in Native": name_text,
                    "coordinates": [[name_coordinates[0][0], name_coordinates[0][1], name_coordinates[0][2], name_coordinates[0][3]]]
                }
            return result
        except Exception as e:
            self.logger.error(f"| Aadhaar Name in Native: {e}")
            return result

    def _extract_palces(self):
        result = {
            "Aadhaar Place Name": "",
            "coordinates": []
            }
        try:
            place_name = ""
            place_coordinates = []

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates_default):
                for state_pattern in self.states:
                    if re.search(state_pattern, text, re.IGNORECASE):
                        place_coordinates.append([x1, y1, x2, y2])
                        place_name += " "+ text

            if not place_coordinates:
                return result
        
            result = {
                "Aadhaar Place Name": place_name,
                "coordinates": place_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"| Aadhaar Place Name: {e}")
            return result
    
    def _extract_pin_code(self):
        result = {
            "Aadhaar Pincode": "",
            "coordinates": []
            }
        try:
            pin_code = ""
            pin_code_coordinates = []
            get_coords_result = []

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates_default):
                if len(text) == 6 and text.isdigit():
                    pin_code_coordinates.append([x1, y1, x2, y2])
                    pin_code = text
                    break
            if not pin_code_coordinates:
                return result
        
            for i in pin_code_coordinates:
                coords_result = self._get_first_3_chars(i)
                get_coords_result.append(coords_result)

            result = {
                "Aadhaar Pincode": pin_code,
                "coordinates": get_coords_result
            }
            return result
        except Exception as error:
            self.logger.error(f"Error: Aadhaar Pincode | {error}")
            return result

    def _get_first_3_chars(self, coords: list) -> list:
        width = coords[2] - coords[0]
        result = [coords[0], coords[1], coords[0] + int(0.30 * width), coords[3]]
        return result

    def _extract_qrcode(self):
        result = {
            "Aadhaar QR Code": "",
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
                "Aadhaar QR Code": f"Found {len(qrcode_coordinates)} QR Codes",
                "coordinates": qrcode_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"E-Aadhaar QR Code: {e}")
            return result


    def collect_aadhaarcard_info(self):
        aadhaarcard_doc_info_list = []
        try:
            """Get the redaction level"""
            if self.DOCUMENT_REDACTION_LEVEL == 1:

                """Collect DOB"""
                dob = self._extract_dob()
                aadhaarcard_doc_info_list.append(dob)

                """Collect Gender"""
                gender = self._extract_gender()
                aadhaarcard_doc_info_list.append(gender)

                """Collect Aadhaar Number"""
                aadhaar_number = self._extract_aadhaar_number()
                aadhaarcard_doc_info_list.append(aadhaar_number)

                """Collect Name in english"""
                aadhaar_name_eng = self._extract_name_in_eng()
                aadhaarcard_doc_info_list.append(aadhaar_name_eng)

                """Collect Name in native language"""
                aadhaar_name_native = self._extract_name_in_native()
                aadhaarcard_doc_info_list.append(aadhaar_name_native)

                """Collect Place name"""
                place_name = self._extract_palces()
                aadhaarcard_doc_info_list.append(place_name)

                """Collect Pincode"""
                pincode = self._extract_pin_code()
                aadhaarcard_doc_info_list.append(pincode)

                """Collect QR-Codes"""
                qrcode = self._extract_qrcode()
                aadhaarcard_doc_info_list.append(qrcode)

                """Check if all the dictionaries in the list are empty"""
                all_keys_and_coordinates_empty =  all(all(not v for v in d.values()) for d in aadhaarcard_doc_info_list)
                if all_keys_and_coordinates_empty:
                    self.logger.error(f"| Unable to extract Aadhaar document information")
                    return {"message": "Unable to extract Aadhaar document information", "status": "REJECTED"}
                else:
                    self.logger.info(f"| Successfully Redacted Aadhaar Document")
                    return {"message": "Successfully Redacted Aadhaar Document", "status": "REDACTED", "data": aadhaarcard_doc_info_list}
            else:

                """Collect DOB"""
                dob = self._extract_dob()
                if len(dob['coordinates']) == 0:
                    self.logger.error("| Aadhaar Card DOB not found")
                    return {"message": "Unable to extract DOB from Aadhaar Document", "status": "REJECTED"}
                aadhaarcard_doc_info_list.append(dob)

                """Collect Gender"""
                gender = self._extract_gender()
                if len(gender['coordinates']) == 0:
                    self.logger.error("| Aadhaar Card Gender not found")
                    return {"message": "Unable to extract Gender from Aadhaar Document", "status": "REJECTED"}
                aadhaarcard_doc_info_list.append(gender)

                """Collect Aadhaar Number"""
                aadhaar_number = self._extract_aadhaar_number()
                if len(aadhaar_number['coordinates']) == 0:
                    self.logger.error("| Aadhaar Card Number not found")
                    return {"message": "Unable to extract Aadhaar Number", "status": "REJECTED"}
                aadhaarcard_doc_info_list.append(aadhaar_number)

                """Collect Name in english"""
                aadhaar_name_eng = self._extract_name_in_eng()
                if len(aadhaar_name_eng['coordinates']) == 0:
                    self.logger.error("| Aadhaar Card name in english not found")
                    return {"message": "Unable to extract Aadhaar Name in english", "status": "REJECTED"}
                aadhaarcard_doc_info_list.append(aadhaar_name_eng)

                """Collect Name in native language"""
                aadhaar_name_native = self._extract_name_in_native()
                if len(aadhaar_name_native['coordinates']) == 0:
                    self.logger.error("| Aadhaar Card name in native language not found")
                    return {"message": "Unable to extract Aadhaar Name in native language", "status": "REJECTED"}
                aadhaarcard_doc_info_list.append(aadhaar_name_native)

                """Collect Place name"""
                place_name = self._extract_palces()
                aadhaarcard_doc_info_list.append(place_name)

                """Collect Pincode"""
                pincode = self._extract_pin_code()
                aadhaarcard_doc_info_list.append(pincode)

                """Collect QR-Codes"""
                qrcode = self._extract_qrcode()
                aadhaarcard_doc_info_list.append(qrcode)

                self.logger.info(f"| Successfully Redacted Aadhaar Document")
                return {"message": "Successfully Redacted Aadhaar Document", "status": "REDACTED", "data": aadhaarcard_doc_info_list}
                
        except Exception as e:
            self.logger.error(f"| Collecting Aadhaar document information: {e}")
            return {"message": "Error collecting Aadhaar document information", "status": "REJECTED"}
