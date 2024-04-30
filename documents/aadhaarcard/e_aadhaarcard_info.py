import re
import cv2
import datetime
import configparser
import pytesseract
from qreader import QReader
from helper.extract_text_coordinates import TextCoordinates
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from config.indian_places import indian_states_cities

class EAadhaarCardDocumentInfo:
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
        tesseract_config = r'--oem 3 --psm 11'
        self.coordinates = TextCoordinates(self.document_path, lang_type=None).generate_text_coordinates()
        self.text_data_none = pytesseract.image_to_string(self.document_path, lang="eng", config=tesseract_config)
        self.coordinates_default = TextCoordinates(self.document_path, lang_type="default").generate_text_coordinates()
        self.coordinates_regional = TextCoordinates(self.document_path, lang_type="regional").generate_text_coordinates()
        self.text_data_default = pytesseract.image_to_string(self.document_path)
        self.text_data_regional = pytesseract.image_to_string(self.document_path, lang="hin+eng", config=tesseract_config)
        
        
    def _extract_dob(self) -> dict:
        result = {
            "E-Aadhaar DOB": "",
            "coordinates": []
        }
        try:
            dob_text = ""
            dob_coordinates = []
            dob_coords = []
            date_pattern = r'\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}|\d{4}|\d{2}/\d{4}|\d{2}/\d{2}|\d{4}/\d{4}'

            print(self.coordinates_default)
            for i, (x1, y1, x2, y2, text) in enumerate(self.coordinates_default):
                match = re.search(date_pattern, text) or re.search(r'\d{8}', text)
                if match:
                    if "-" in text:
                        split_pattern = "-"
                    else:
                        split_pattern = "/"
                    
                    if self._validate_date(text, split_pattern):
                        dob_coords.append([x1, y1, x2, y2])
                        dob_text += " "+ text
                        
            if not dob_coords:
                print(self.coordinates)
                """Check with other coordinates"""
                for i, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
                    match = re.search(date_pattern, text) or re.search(r'\d{8}', text)
                    if match:
                        if "-" in text:
                            split_pattern = "-"
                        else:
                            split_pattern = "/"

                        if self._validate_date(text, split_pattern):
                             dob_coords.append([x1, y1, x2, y2])
                             dob_text += " "+ text

                if not dob_coords:
                    return result
                
            for i in dob_coords:
                """Get the first 6 chars coordinates"""
                width = i[2] - i[0]
                dob_coordinates.append([i[0], i[1], i[0] + int(0.54 * width), i[3]])

            result = {
                "E-Aadhaar DOB": dob_text,
                "coordinates": dob_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"| E-Aadhaar DOB: {e}")
            return result
    
    def _validate_date(self, date_str: str, split_pattern: str) -> bool:
        try:
            
            # Split the date string into day, month, and year
            day, month, year = map(int, date_str.split('/'))
            
            # Check if the date is within valid ranges
            if not (1 <= day <= 31 and 1 <= month <= 12 and 1000 <= year <= 2999):
                return False
            
            # Check for leap year if necessary
            if month == 2 and day > 28 and not (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
                return False
            # # Create a datetime object to validate the date
            datetime.datetime(year, month, day)
            return True
        except Exception as e:
            return False
    
    def _extract_gender(self):
        result = {
            "E-Aadhaar Gender": "",
            "coordinates": []
        }
        try:
            gender_text = ""
            gender_coordinates = []
            coordinates = self.coordinates_default
            
            """Get the matching index number of gender"""
            for i ,(x1,y1,x2,y2,text) in enumerate(coordinates):
                if text.lower() in ["male", "female", "femalp", "femala", "mala", "femate", "#femste","fomale", "fertale", "malo", "femsle", "fade", "ferme", "famate"]:
                    if coordinates[i -1][4] == "/":
                        gender_coordinates = [coordinates[i -2][0], coordinates[i -2][1], x2, y2]
                        gender_text = text
                    else:
                        gender_coordinates = [coordinates[i -1][0], coordinates[i -1][1], x2, y2]
                        gender_text = text     
                    break

            if not gender_coordinates:
                coordinates = self.coordinates
                
                """Try with self.coordinates"""
                for i,(x1,y1,x2,y2,text) in enumerate(coordinates):
                    if text.lower() in  ["male", "female", "femalp", "femala", "mala", "femate", "#femste", "fomale", "fertale", "malo","femsle", "fade", "ferme", "famate"]:
                        if coordinates[i -1][4] == "/":
                            gender_coordinates = [coordinates[i -2][0], coordinates[i -2][1], x2, y2]
                            gender_text = text
                        else:
                            gender_coordinates = [coordinates[i -1][0], coordinates[i -1][1], x2, y2]
                            gender_text = text
                        break
                if not gender_coordinates:
                    return result
                
            result = {
                "E-Aadhaar Gender": gender_text,
                "coordinates": [gender_coordinates]
            }
            return result
        except Exception as e:
            self.logger.error(f"| E-Aadhaar Gender: {e}")
            return result
    
    def _extract_aadhaar_number(self):
        result = {
            "E-Aadhaar Number": "",
            "coordinates": []
        }
        try:
            aadhaar_number_text = ""
            aadhaar_number_coordinates = []
            aadhaar_number_text_coords = []
            matching_index = None
            coordinates = self.coordinates

            """Get the gender index"""
            for i,(x1,y1,x2,y2,text) in enumerate(coordinates):
                if text.lower() in ["male", "female", "femalp", "femala", "mala", "femate","femsle","#femste","fomale", "fertale", "malo", "fade", "ferme", "famate"]:
                    matching_index = i
                    break
            if matching_index is None:
                coordinates = self.coordinates_default
                for i,(x1, y1, x2, y2, text) in enumerate(coordinates):
                    if text.lower() in ["male", "female", "femalp", "femala", "mala", "femate", "#femste", "fomale", "fertale", "malo","femsle", "fade", "ferme", "famate"]:
                        matching_index = i
                        break
                if matching_index is None:
                    return result

            """Get the coordinates"""
            for i in range(matching_index, len(coordinates)):
                text = coordinates[i][4]
                if len(text) == 4 and text.isdigit() and text[:2] != '19':
                    aadhaar_number_text_coords.append((text))
                    aadhaar_number_text += " "+ text
                if len(aadhaar_number_text_coords) == 3:
                    break
            
            if not aadhaar_number_text_coords:
                return result
            
            if len(aadhaar_number_text_coords) > 1:
                aadhaar_number_text_coords =aadhaar_number_text_coords[:-1]

            for i in aadhaar_number_text_coords:
                for k,(x1,y1,x2,y2,text) in enumerate(coordinates):
                    if i == text:
                        aadhaar_number_coordinates.append([x1,y1,x2,y2])
            result = {
                "E-Aadhaar Number": aadhaar_number_text,
                "coordinates": aadhaar_number_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"| E-Aadhaar Number: {e}")
            return result
        
    def _extract_name_in_english(self):
        result = {
            "E-Aadhaar Name in English": "",
            "coordinates": []
        }
        try:
            name_coordinates = []
            matching_text = ""
            matching_text_top = []
            matching_text_bottom = []

            #clean_text = [i for i in self.text_data_default.split("\n") if len(i) != 0]
            clean_text = [i for i in self.text_data_none.split("\n") if len(i) != 0]
            
            # def contains_keyword(text, keywords):
            #     for keyword in keywords:
            #         if keyword.lower() in text.lower():
            #             return True
            #     return False
            
            """Get Name from Top"""
            match_1_keywords = ["ace", "ta", "ata arate tahar", "ata", "arate", "tahar", "to", "to,", "ta", "to.","jo"]
            match_to_keywords = ["ta", "to", "to,", "to.", "tahar","jo"]
            print(clean_text)
            for i, text in enumerate(clean_text):
                if text.lower() in match_1_keywords:
                    if clean_text[i + 1].lower() in match_to_keywords:
                        matching_text_top = clean_text[i + 3].split()
                    else:
                        keywords_regex = r"\b(?:aadhaar|proof|proot|identity|citizenship)\b"
                        if re.search(keywords_regex, clean_text[i + 1], flags=re.IGNORECASE):
                            matching_text_top = clean_text[i + 3].split()
                        else:
                            matching_text_top = clean_text[i + 1].split()
                    break

            """Get the coordinates"""
            if matching_text_top:
                if len(matching_text_top) > 1:
                    matching_text_top = matching_text_top[: -1]
                
                for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                    if text in matching_text_top:
                        name_coordinates.append([x1, y1, x2, y2])
            
            """Get Name from Bottom"""
            keywords_regex = r"\b(?:dob|birth|bith|year|dou|binh|008|pub|farce|binn|yoas|dou|doe)\b"
            #match_2_keywords = ["year", "dob", "birth", "bith","binh","dou","doe", "fest", "fahy"]
            for i, text in enumerate(clean_text):
                if re.search(keywords_regex, text.lower(), flags=re.IGNORECASE):
                    if len(clean_text[i -1]) == 1:
                        matching_text_bottom = clean_text[i -2].split()
                    else:
                        matching_text_bottom = clean_text[i -1].split()
                    break
            
            if not matching_text_top and not matching_text_bottom:
                return result
            
            """Get the coordinates"""
            if len(matching_text_bottom) > 1:
                matching_text_bottom = matching_text_bottom[:-1]

            for i, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if text in matching_text_bottom:
                    name_coordinates.append([x1, y1, x2, y2])

            if matching_text_top:
                matching_text = " ".join(matching_text_top)
            else:
                matching_text = " ".join(matching_text_bottom)

            result = {
                "E-Aadhaar Name in English": matching_text,
                "coordinates": name_coordinates
                }
            return result
        except Exception as e:
            self.logger.error(f"| E-Aadhaar Name in English: {e}")
            return result
        
    def _extact_name_in_native(self):
        result = {
            "E-Aadhaar Name in Native": "",
            "coordinates": []
        }
        try:
            name_coordinates = []
            matching_text = ""
            matching_text_top = []
            matching_text_bottom = []

            clean_text_default = [i for i in self.text_data_none.split("\n") if len(i) != 0]
            #clean_text_default = [i for i in self.text_data_default.split("\n") if len(i) != 0]
            """Get Name from Top"""
            match_1_keywords = ["tahar", "to", "to,", "ta", "to.","jo"]
            for i, text in enumerate(clean_text_default):
                if text.lower() in match_1_keywords:
                    matching_text_top = clean_text_default[i + 2].split()
                    break
            
            """Get the Coordinates"""
            if matching_text_top:
                if len(matching_text_top) > 1:
                    top_matching_text = " ".join(matching_text_top)
                    matching_text_top = matching_text_top[:-1]
                
                for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                    if text in matching_text_top:
                        name_coordinates.append([x1, y1, x2, y2])
            
            """Get Name from Bottom"""
            keywords_regex = r"\b(?:dob|birth|bith|year|dou|binh|008|pub|farce|binn|yoas|dou|doe)\b"
            #keywords_regex = r"\b(?:dob|birth|bith|year|dou|binh|008|pub|farce|binn|yoas)\b"
            for i,text in enumerate(clean_text_default):
                if re.search(keywords_regex, text.lower(), flags=re.IGNORECASE):
                    matching_text_bottom = clean_text_default[i -2].split()
                    break

            """Get the Coordinates"""
            if not matching_text_top and not matching_text_bottom:
                return result
            
            if len(matching_text_bottom) > 1:
                bottom_matching_text = " ".join(matching_text_bottom)
                matching_text_bottom = matching_text_bottom[:-1]
            
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if text in matching_text_bottom:
                    name_coordinates.append([x1, y1, x2, y2])

            if matching_text_top:
                matching_text = top_matching_text
            else:
                matching_text = bottom_matching_text

            result = {
                "E-Aadhaar Name in Native": matching_text,
                "coordinates": name_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"| E-Aadhaar Name in Native: {e}")
            return result

    def _extract_mobile_number(self):
        result = {
            "E-Aadhaar Mobile Number": "",
            "coordinates": []
            }
        try:
            mobile_number = ""
            mobile_coordinates = []

            """get the coordinates"""
            for i,(x1, y1, x2, y2,text) in enumerate(self.coordinates):
                if len(text) in (10,11) and text[:10].isdigit():
                    mobile_coordinates = [x1, y1, x2, y2]
                    mobile_number = text
                    break
            if not mobile_coordinates:
                return result
        
            """get first 6 chars"""
            width = mobile_coordinates[2] - mobile_coordinates[0]
            result = {
                "E-Aadhaar Mobile Number" : mobile_number,
                "coordinates" : [[mobile_coordinates[0], mobile_coordinates[1], mobile_coordinates[0] + int(0.54 * width), mobile_coordinates[3]]]
            }
            return result
        except Exception as e:
            self.logger.error(f"| E-Aadhaar Mobile Number: {e}")
            return result
        
    def _extract_pin_code(self):
        result = {
            "E-Aadhaar Pincode": "",
            "coordinates": []
            }
        try:
            pin_code = ""
            pin_code_coordinates = []
            get_coords_result = []

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if len(text) in (6,7) and text[:6].isdigit():
                    pin_code_coordinates.append([x1, y1, x2, y2])
                    pin_code += " "+ text
            if not pin_code_coordinates:
                return result
        
            for i in pin_code_coordinates:
                coords_result = self._get_first_3_chars(i)
                get_coords_result.append(coords_result)

            result = {
                "E-Aadhaar Pincode": pin_code,
                "coordinates": get_coords_result
            }
            return result
        except Exception as e:
            self.logger.error(f"| E-Aadhaar Pincode: {e}")
            return result
        
    def _get_first_3_chars(self, coords: list) -> list:
        width = coords[2] - coords[0]
        result = [coords[0], coords[1], coords[0] + int(0.30 * width), coords[3]]
        return result
    
    def _extract_palces(self):
        result = {
            "E-Aadhaar Place Name": "",
            "coordinates": []
            }
        try:
            place_name = ""
            place_coordinates = []
            
            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                for state_pattern in self.states:
                    if re.search(state_pattern, text, re.IGNORECASE) and text.lower() not in ["electronically", 'electronica.ly', 'sitrongs']:
                        place_coordinates.append([x1, y1, x2, y2])
                        place_name += " "+ text
                        
            if not place_coordinates:
                return result
        
            result = {
                "E-Aadhaar Place Name": place_name,
                "coordinates": place_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"| E-Aadhaar Place Name: {e}")
            return result
        
    def _extract_qrcode(self):
        result = {
            "E-Aadhaar QR Code": "",
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
                "E-Aadhaar QR Code": f"Found {len(qrcode_coordinates)} QR Codes",
                "coordinates": qrcode_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"E-Aadhaar QR Code: {e}")
            return result

    def collect_e_aadhaarcard_info(self):
        e_aadhaarcard_doc_info_list = []
        try:
            """Get the redaction level"""
            if self.DOCUMENT_REDACTION_LEVEL == 1:

                """Collect DOB"""
                dob = self._extract_dob()
                e_aadhaarcard_doc_info_list.append(dob)

                """Collect Gender"""
                gender = self._extract_gender()
                e_aadhaarcard_doc_info_list.append(gender)

                """Collect Aadhaar Number"""
                aadhaar_number = self._extract_aadhaar_number()
                e_aadhaarcard_doc_info_list.append(aadhaar_number)

                """Collect Name in english"""
                name_in_eng = self._extract_name_in_english()
                
                e_aadhaarcard_doc_info_list.append(name_in_eng)

                """Collect Name in native"""
                name_in_native = self._extact_name_in_native()
                e_aadhaarcard_doc_info_list.append(name_in_native)

                """Collect Mobile number"""
                mobile_number = self._extract_mobile_number()
                e_aadhaarcard_doc_info_list.append(mobile_number)

                """Collect Pin code"""
                pincode = self._extract_pin_code()
                e_aadhaarcard_doc_info_list.append(pincode)

                """Collect Place name"""
                places = self._extract_palces()
                e_aadhaarcard_doc_info_list.append(places)

                """Collect QR-Code"""
                qrcodes = self._extract_qrcode()
                e_aadhaarcard_doc_info_list.append(qrcodes)

                """Check if all the dictionaries in the list are empty"""
                all_keys_and_coordinates_empty =  all(all(not v for v in d.values()) for d in e_aadhaarcard_doc_info_list)
                if all_keys_and_coordinates_empty:
                    self.logger.error(f"| Unable to extract E-Aadhaar document information")
                    return {"message": "Unable to extract E-Aadhaar document information", "status": "REJECTED"}
                else:
                    self.logger.info(f"| Successfully Redacted E-Aadhaar Document")
                    return {"message": "Successfully Redacted E-Aadhaar Document", "status": "REDACTED", "data": e_aadhaarcard_doc_info_list}
            else:

                """Collect DOB"""
                dob = self._extract_dob()
                if len(dob['coordinates']) == 0:
                    self.logger.error("| E-Aadhaar Card DOB not found")
                    return {"message": "Unable to extract DOB from E-Aadhaar Document", "status": "REJECTED"}
                e_aadhaarcard_doc_info_list.append(dob)

                """Collect Gender"""
                gender = self._extract_gender()
                if len(gender['coordinates']) == 0:
                    self.logger.error("| E-Aadhaar Card Gender not found")
                    return {"message": "Unable to extract gender from E-Aadhaar Document", "status": "REJECTED"}
                e_aadhaarcard_doc_info_list.append(gender)

                """Collect Aadhaar Number"""
                aadhaar_number = self._extract_aadhaar_number()
                if len(aadhaar_number['coordinates']) == 0:
                    self.logger.error("| E-Aadhaar Card Number not found")
                    return {"message": "Unable to extract aadhaar card number", "status": "REJECTED"}
                e_aadhaarcard_doc_info_list.append(aadhaar_number)

                """Collect Name in english"""
                name_in_eng = self._extract_name_in_english()
                if len(name_in_eng['coordinates']) == 0:
                    self.logger.error("| E-Aadhaar Card Name in english not found")
                    return {"message": "Unable to extract name in english from E-Aaadhaar Document", "status": "REJECTED"}
                e_aadhaarcard_doc_info_list.append(name_in_eng)

                """Collect Name in native"""
                name_in_native = self._extact_name_in_native()
                if len(name_in_native['coordinates']) == 0:
                    self.logger.error("| E-Aadhaar Card Name in regional language not found")
                    return {"message": "Unable to extract name in regional from E-Aadhaar Document", "status": "REJECTED"}
                e_aadhaarcard_doc_info_list.append(name_in_native)

                """Collect Mobile number"""
                mobile_number = self._extract_mobile_number()
                if len(mobile_number['coordinates']) == 0:
                    self.logger.error("| E-Aadhaar Mobile Number not found")
                    return {"message": "Unable to extract aadhaar mobile number", "status": "REJECTED"}
                e_aadhaarcard_doc_info_list.append(mobile_number)

                """Collect Pin code"""
                pincode = self._extract_pin_code()
                if len(pincode['coordinates']) == 0:
                    self.logger.error("| E-Aadhaar Card Pincode not found")
                    return {"message": "Unable to extract aadhaar pincode", "status": "REJECTED"}
                e_aadhaarcard_doc_info_list.append(pincode)

                """Collect Place name"""
                places = self._extract_palces()
                e_aadhaarcard_doc_info_list.append(places)

                """Collect QR-Code"""
                qrcodes = self._extract_qrcode()
                e_aadhaarcard_doc_info_list.append(qrcodes)
                
                self.logger.info(f"| Successfully Redacted E-Aadhaar Document")
                return {"message": "Successfully Redacted E-Aadhaar Document", "status": "REDACTED", "data": e_aadhaarcard_doc_info_list}
        except Exception as e:
            self.logger.error(f"| Collecting E-Aadhaar document information: {e}")
            return {"message": "Error collecting E-Aadhaar document information", "status": "REJECTED"}


        
    