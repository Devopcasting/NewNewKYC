import re
import configparser
import pytesseract
from helper.passport_text_coordinates import TextCoordinates
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from config.indian_places import indian_states_cities

class PassportDocumentInfo:
    def __init__(self, document_path: str) -> None:
        self.document_path = document_path
        self._load_configuration()
        self._setup_logging()
        self._extract_text_coordinates()
        self.states = indian_states_cities

    def _load_configuration(self):
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(r'C:\Program Files (x86)\OCRR\config\configuration.ini')
        self.DOCUMENT_REDACTION_LEVEL = int(config['Level']['RedactionLevel'])

    def _setup_logging(self):
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()
    
    def _extract_text_coordinates(self):
        self.coordinates = TextCoordinates(self.document_path).generate_text_coordinates()
        self.coordinates_default = TextCoordinates(self.document_path, lang_type="default").generate_text_coordinates()
        tesseract_config = r'--oem 3 --psm 11'
        self.text_data = pytesseract.image_to_string(self.document_path, lang="eng", config=tesseract_config)
        
        
    def _extract_passport_number(self):
        result = {
            "Passport Number": "",
            "coordinates": []
            }
        try:
            passport_number = ""
            matching_line_index = None
            matching_text_regex =  r"\b(?:jpassport|passport|pusepart|passpon|paasport|ipassport|pasaport|posspau|passgert)\b"
            passport_number_coordinates = []

            """find matching text index"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if re.search(matching_text_regex, text.lower(), flags=re.IGNORECASE):
                    matching_line_index = i
                    break
            
            check_passport_string = lambda s: re.match(r'^[A-Z][0-9]{7}$', s) is not None
            if matching_line_index is None:
                """Direct check"""
                for i,(x1,y1,x2,y2,text) in enumerate(self.coordinates):
                    if check_passport_string(text):
                        passport_number_coordinates = [x1, y1, x2, y2]
                        passport_number = text
                        break
                if not passport_number_coordinates:
                    """Check for 8 digit number"""
                    for i,(x1,y1,x2,y2,text) in enumerate(self.coordinates):
                        if len(text) in (6,7,8) and text.isdigit():
                            passport_number = text
                            passport_number_coordinates = [x1, y1, x2, y2]
                            break
                    if not passport_number_coordinates:
                        return result
            else:
                valid_characters = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
                for i in range(matching_line_index, len(self.coordinates)):
                    text = self.coordinates[i][4]
                    all_valid_characters = any(char in valid_characters for char in text[1:])
                    if len(text) == 8 and text[0].isalpha() and text[0].isupper() and all_valid_characters:
                        passport_number = text
                        passport_number_coordinates = [self.coordinates[i][0], self.coordinates[i][1],
                                                       self.coordinates[i][2], self.coordinates[i][3]]
                        break
                    elif len(text) in (6,7,8) and text.isupper() and text.isdigit():
                        passport_number = text
                        passport_number_coordinates = [self.coordinates[i][0], self.coordinates[i][1],
                                                       self.coordinates[i][2], self.coordinates[i][3]]
                        break
                    elif len(text) in (6,7,8) and text.isdigit():
                        passport_number = text
                        passport_number_coordinates = [self.coordinates[i][0], self.coordinates[i][1],
                                                       self.coordinates[i][2], self.coordinates[i][3]]
                        break
                
                if not passport_number_coordinates:
                    return result
            
            result = {
                "Passport Number": passport_number,
                "coordinates": [passport_number_coordinates]
                    }
            return result
        except Exception as e:
            self.logger.error(f"| Passport Number: {e}")
            return result
    
    def _extract_dates(self):
        result = {
            "Passport Dates": "",
            "coordinates": []
            }
        try:
            date_text = ""
            date_coords = []
            date_coordinates = []

            """date patterns for both dd/mm/yyyy and dd/mm/yy formats"""
            date_pattern = r'\d{2}/\d{2}/\d{4}|\d{2}/\d{2}/\d{2}|\d{4}/\d{4}'

            """get the coordinates"""
            for i, (x1,y1,x2,y2,text) in enumerate(self.coordinates):
                date_match = re.search(date_pattern, text)
                if date_match:
                    date_coords.append([x1, y1, x2, y2])
                    date_text += " "+ text
        
            if not date_coords:
                return result
        
            """get the first 6 chars"""
            for i in date_coords:
                width = i[2] - i[0]
                date_coordinates.append([i[0], i[1], i[0] + int(0.54 * width), i[3]])
            
            result = {
                "Passport Dates": date_text,
                "coordinates": date_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"| Passport Dates: {e}")
            return result
        
    def _extract_gender(self):
        result = {
            "Passport Gender": "",
            "coordinates": []
            }
        try:
            gender_text = ""
            matching_text_keyword = ['M', 'F', 'MALE', 'FEMALE']
            gender_coordinates = []

            """get the coordinates"""
            for i, (x1,y1,x2,y2,text) in enumerate(self.coordinates):
                if text in matching_text_keyword:
                    gender_coordinates = [x1, y1, x2, y2]
                    gender_text = text
                    break
            if not gender_coordinates:
                return result
        
            result = {
                "Passport Gender": gender_text,
                "coordinates": [gender_coordinates]
            }
            return result
        except Exception as e:
            self.logger.error(f"| Passport Gender: {e}")
            return result
        
    def _extract_surname(self):
        result = {
            "Passport Surname": "",
            "coordinates": []
            }
        try:
            surname_text = ""
            surname_coords = []
            surname_coordinates = []
            matching_line_index = None
            matching_text_regex =  r"\b(?:surname|suname|surmame|sumame|ssurmame|weesenet|canam|sumsme|senane|surnane)\b"

            
            """find matching text index"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if re.search(matching_text_regex, text.lower(), flags=re.IGNORECASE):
                    matching_line_index = i
                    break
            if matching_line_index is None:
                return result
            
            """get the surname coordinates"""
            for i in range(matching_line_index, len(self.coordinates)):
                text = self.coordinates[i][4]
                contains_no_numbers = lambda text: not bool(re.search(r'\d', text))
                if text.isupper() and contains_no_numbers(text) and text != "SS" and text != "IND":
                    surname_coords = [self.coordinates[i][0], self.coordinates[i][1],
                                         self.coordinates[i][2], self.coordinates[i][3]]
                    surname_text = text
                    break 
            if not surname_coords:
                return result
            
            width = surname_coords[2] - surname_coords[0]
            surname_coordinates.append([surname_coords[0], surname_coords[1], surname_coords[0] + int(0.40 * width), surname_coords[3]])
    
            result = {
                "Passport Surname": surname_text,
                "coordinates": surname_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"| Passport Surname: {e}")
            return result

    def _extract_given_name(self):
        result = {
            "Passport Given Name": "",
            "coordinates": []
            }
        try:
            given_name_text = ""
            given_name_cords = []
            matching_line_index = None
            given_name_coordinates = []
            matching_text_regex =  r"\b(?:given|giver|igiven|ghee|grven|geen|glen)\b"
        
            """find matching text index"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if re.search(matching_text_regex, text.lower(), flags=re.IGNORECASE):
                    matching_line_index = i
                    break
            if matching_line_index is None:
                return result
        
            """get the coordinates"""
            matching_given_regex = r"\b(?:given|giver|igiven|ghee|grven|name|geen|hote|ga|seouse|norms|namen|glen)\b"
            for i in range(matching_line_index, len(self.coordinates)):
                text = self.coordinates[i][4]
                if text.lower() in ["eo","of","pat","ste","fam","wessex","ea", "ms", "fi", "ee", 
                                    "fort", "wef", "ly", "fin", "/sex", "sax","indian","wen",
                                    "wanfafa","dore","fier","sex","pl","ie","i3ex","wafers",
                                    "pepo","or","ent","seal","fer","reiaar", "nationailty", "et", "bg", "ange", "bir","indian"]:
                    break
                if text.isupper() or text[0].isupper() and text.lower() not in ["gra", "glen", "heoecgap"]:
                    if not re.search(matching_given_regex, text.lower(), flags=re.IGNORECASE):
                        given_name_cords.append([self.coordinates[i][0], self.coordinates[i][1], self.coordinates[i][2], self.coordinates[i][3]])
                        given_name_text += " "+text
            
            if len(given_name_cords) > 1:
                given_name_cords = given_name_cords[:-1]

            for i in given_name_cords:
                given_name_coordinates.append([i[0], i[1], i[2], i[3]])
        
            result = {
                "Passport Given Name": given_name_text,
                "coordinates": given_name_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"| Passport Given Name: {e}")
            return result
        
    def _extract_father_name(self):
        result = {
            "Passport Father Name": "",
            "coordinates": []
            }
        try:
            
            father_name_text = ""
            matching_text_regex =  r"\b(?:father|legal|guardian)\b"
            father_name_coords = []
            father_name_coordinates = []
            matching_line_index = None

            """find matching text index"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if re.search(matching_text_regex, text.lower(), flags=re.IGNORECASE):
                    matching_line_index = i
                    break
            if matching_line_index is None:
                return result
        
            """get the coordinates"""
            for i in range(matching_line_index, len(self.coordinates)):
                text = self.coordinates[i][4]
                if text.lower() in ["aren", "ast", "sa", "area", "ant", "any", '"name', "/name", "of", "mother", "ware", "an", "wim", "rope"]:
                        break
                if text.isupper() and text not in self.states:
                    father_name_coords.append([self.coordinates[i][0], self.coordinates[i][1], self.coordinates[i][2], self.coordinates[i][3]])
                    father_name_text += " "+text
                    
            for i in father_name_coords:
                width = i[2] - i[0]
                father_name_coordinates.append([i[0], i[1], i[0] + int(0.40 * width), i[3]])
        
            result = {
                "Passport Father Name": father_name_text,
                "coordinates": father_name_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"| Passport Father Name: {e}")
            return result
        
    def _extract_mother_name(self):
        result = {
            "Passport Mother Name": "",
            "coordinates": []
            }
        try:
            matching_text_regex =  r"\b(?:mother)\b"
            mother_coords = []
            mother_text = ""
            mother_coordinates = []
            matching_line_index = None
            
            """find matching text index"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if re.search(matching_text_regex, text.lower(), flags=re.IGNORECASE):
                    matching_line_index = i
                    break
            if matching_line_index is None:
                return result
           
            """get the coordinates"""
            for i in range(matching_line_index, len(self.coordinates)):
                text = self.coordinates[i][4]
                if text.lower() in ["af","at","gen", "ar", "ora", "en", "aes","eet", "are", "art", "uct", "mr", "ort"]:
                    break
                if text.isupper():
                    mother_coords.append([self.coordinates[i][0], self.coordinates[i][1], self.coordinates[i][2], self.coordinates[i][3]])
                    mother_text += " "+text
                    
            for i in mother_coords:
                width = i[2] - i[0]
                mother_coordinates.append([i[0], i[1], i[0] + int(0.40 * width), i[3]])
        
            result = {
                "Passport Mother Name": mother_text,
                "coordinates": mother_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"| Passport Mother Name: {e}")
            return result
    
    def _extract_spouse_name(self):
        result = {
            "Passport Spouse Name": "",
            "coordinates": []
        }
        try:
            spouse_name = ""
            matching_line_index = None
            spouse_name_coordinates = []
            spouse_name_coords = []
        
            spouse_regex = r"(?:spouse|seouse)"
            """find matching text index"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if re.search(spouse_regex, text.lower(), flags=re.IGNORECASE):
                    matching_line_index = i
                    break
            if matching_line_index is None:
                return result
           
            """get the coordinates"""
            for i in range(matching_line_index, len(self.coordinates)):
                text = self.coordinates[i][4]
                if text.lower() in ["um", "address"]:
                    break
                if text.isupper():
                    spouse_name_coords.append([self.coordinates[i][0], self.coordinates[i][1], self.coordinates[i][2], self.coordinates[i][3]])
                    spouse_name += " "+text
                    
            for i in spouse_name_coords:
                width = i[2] - i[0]
                spouse_name_coordinates.append([i[0], i[1], i[0] + int(0.40 * width), i[3]])
        
            result = {
                "Passport Spouse Name": spouse_name,
                "coordinates": spouse_name_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"| Passport Spouse Name: {e}")
            return result
        
    def _extract_ind_name(self):
        result = {
            "Passport IND Name": "",
            "coordinates": []
            }
        try:
            ind_name_text = ""
            ind_name_cords = []
            ind_name_coordinates = []
            #ind_check_list = ["IND", "END"]
            ind_check_list = ["<"]

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if any(string in text for string in ind_check_list):
                    ind_name_cords.append([x1, y1, x2, y2])
                    ind_name_text += " "+text
            if not ind_name_cords:
                return result
            
            if len(ind_name_cords) > 1:
                ind_name_cords = ind_name_cords[:-1]

            for i in ind_name_cords:
                width = i[2] - i[0]
                ind_name_coordinates.append([i[0], i[1], i[0] + int(0.40 * width), i[3]])
        
            result = {
                "Passport IND Name": ind_name_text,
                "coordinates": ind_name_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"| Passport IND Name: {e}")
            return result
        
    def _extract_pincode(self):
        result = {
            "Passport Pincode": "",
            "coordinates": []
            }
        try:
            pincode_number = ""
            pincode_coordinates = []
            pincode_coords = []

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if len(text) == 6 and text.isdigit():
                    pincode_coords.append([x1, y1, x2, y2])
                    pincode_number += " "+text
                    break
            if not pincode_coords:
                return result
            
            for i in pincode_coords:
                width = i[2] - i[0]
                pincode_coordinates.append([i[0], i[1], i[0] + int(0.30 * width), i[3]])
        
            result = {
                "Passport Pincode": pincode_number,
                "coordinates": pincode_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"| Passport Pincode: {e}")
            return result

    def _extract_place(self):
        result = {
            "Passport Place": "",
            "coordinates": []
            }
        try:
            state_name = ""
            state_coordinates = []
            
            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                for state_pattern in self.states:
                    if re.search(state_pattern, text, re.IGNORECASE):
                        state_coordinates.append([x1, y1, x2, y2])
                        state_name += " "+ text
            if not state_coordinates:
                return result
            
            result = {
                "Passport Place": state_name,
                "coordinates": state_coordinates
            }
            
            return result
        except Exception as e:
            self.logger.error(f"| Passport Place: {e}")
            return result
        
    def collect_passport_document_info(self):
        passport_doc_info_list = []

        try:
            if self.DOCUMENT_REDACTION_LEVEL == 1:

                """Collect Passport number"""
                passport_number = self._extract_passport_number()
                passport_doc_info_list.append(passport_number)

                """Collect Dates"""
                passport_dates = self._extract_dates()
                passport_doc_info_list.append(passport_dates)

                """Collect Gender"""
                gender = self._extract_gender()
                passport_doc_info_list.append(gender)

                """Collect Surname"""
                surname = self._extract_surname()
                passport_doc_info_list.append(surname)

                """Collect Given name"""
                given_name = self._extract_given_name()
                passport_doc_info_list.append(given_name)

                """Collect Father name"""
                father_name = self._extract_father_name()
                passport_doc_info_list.append(father_name)

                """Collect Mother name"""
                mother_name = self._extract_mother_name()
                passport_doc_info_list.append(mother_name)

                """Collect IND name"""
                ind_name = self._extract_ind_name()
                passport_doc_info_list.append(ind_name)

                """Collect Spouse name"""
                spouse_name = self._extract_spouse_name()
                passport_doc_info_list.append(spouse_name)

                """Collect Pincode"""
                pincode = self._extract_pincode()
                passport_doc_info_list.append(pincode)

                """Collect Places"""
                places = self._extract_place()
                passport_doc_info_list.append(places)

                """Check if all the dictionaries in the list are empty"""
                all_keys_and_coordinates_empty =  all(all(not v for v in d.values()) for d in passport_doc_info_list)
                if all_keys_and_coordinates_empty:
                    self.logger.error(f"| Unable to extract Passport document information")
                    return {"message": "Unable to extract Passport document information", "status": "REJECTED"}
                else:
                    self.logger.info(f"| Successfully Redacted Passport Document")
                    return {"message": "Successfully Redacted Passport Document", "status": "REDACTED", "data": passport_doc_info_list}
            else:

                """Collect Passport number"""
                passport_number = self._extract_passport_number()
                if len(passport_number['coordinates']) == 0:
                    self.logger.error("| Passport number not found")
                    return {"message": "Unable to extract passport number", "status": "REJECTED"}
                passport_doc_info_list.append(passport_number)

                """Collect Dates"""
                passport_dates = self._extract_dates()
                if len(passport_dates['coordinates']) == 0:
                    self.logger.error("| Passport dates not found")
                    return {"message": "Unable to extract dates from passport document", "status": "REJECTED"}
                passport_doc_info_list.append(passport_dates)

                """Collect Gender"""
                gender = self._extract_gender()
                if len(gender['coordinates']) == 0:
                    self.logger.error("| Passport gender not found")
                    return {"message": "Unable to extract gender from passport", "status": "REJECTED"}
                passport_doc_info_list.append(gender)

                """Collect Surname"""
                surname = self._extract_surname()
                if len(surname['coordinates']) == 0:
                    self.logger.error("| Passport surname not found")
                    return {"message": "Unable to extract surname from passport document", "status": "REJECTED"}
                passport_doc_info_list.append(surname)

                """Collect Given name"""
                given_name = self._extract_given_name()
                if len(given_name['coordinates']) == 0:
                    self.logger.error("| Passport given name not found")
                    return {"message": "Unable to extract given name from passport", "status": "REJECTED"}
                passport_doc_info_list.append(given_name)

                """Collect Father name"""
                father_name = self._extract_father_name()
                if len(father_name['coordinates']) == 0:
                    self.logger.error("| Passport father's name not found")
                    return {"message": "Unable to extract father's name from passport", "status": "REJECTED"}
                passport_doc_info_list.append(father_name)

                """Collect Mother name"""
                mother_name = self._extract_mother_name()
                if len(mother_name['coordinates']) == 0:
                    self.logger.error("| Passport mother name not found")
                    return {"message": "Unable to extract mother name", "status": "REJECTED"}
                passport_doc_info_list.append(mother_name)

                """Collect IND name"""
                ind_name = self._extract_ind_name()
                if len(ind_name['coordinates']) == 0:
                    self.logger.error("| Passport IND name not found")
                    return {"message": "Unable to extract IND name from Passport", "status": "REJECTED"}
                passport_doc_info_list.append(ind_name)

                """Collect Spouse name"""
                spouse_name = self._extract_spouse_name()
                if len(spouse_name['coordinates']) == 0:
                    self.logger.error("| Passport spouse name not found")
                else:
                    passport_doc_info_list.append(spouse_name)
                
                """Collect Pincode"""
                pincode = self._extract_pincode()
                passport_doc_info_list.append(pincode)

                """Collect Places"""
                places = self._extract_place()
                passport_doc_info_list.append(places)

                self.logger.info(f"| Successfully Redacted Passport Document")
                return {"message": "Successfully Redacted Passport Document", "status": "REDACTED", "data": passport_doc_info_list}
        except Exception as e:
            self.logger.error(f"| Collecting Passport document information: {e}")
            return {"message": "Error collecting Passport document information", "status": "REJECTED"}


