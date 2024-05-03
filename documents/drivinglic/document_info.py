import re
import configparser
import pytesseract
from helper.extract_text_coordinates import TextCoordinates
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from config.indian_places import indian_states_cities
from qreader import QReader
import cv2

class DrivingLicenseDocumentInfo:
    def __init__(self, document_path: str) -> None:
        self.document_path = document_path
        self._load_configuration()
        self._setup_logging()
        self._extract_text_coordinates()
        self.states = indian_states_cities
        self.qreader = QReader()

    def _load_configuration(self):
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(r'C:\Program Files (x86)\OCRR\config\configuration.ini')
        self.DOCUMENT_REDACTION_LEVEL = int(config['Level']['RedactionLevel'])

    def _setup_logging(self):
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()
    
    def _extract_text_coordinates(self):
        self.coordinates = TextCoordinates(self.document_path, lang_type="dllang" ).generate_text_coordinates()
        self.text_data = pytesseract.image_to_string(self.document_path, lang="eng")

    def _extract_dl_number(self):
        result = {
            "Driving License Number": "",
            "coordinates": []    
            }
        try:
            dl_number = ""
            dl_number_coordinated = []

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if len(text) == 11 and text.isdigit():
                    dl_number = text
                    dl_number_coordinated.append([x1, y1, x2, y2])
                    break
            if not dl_number_coordinated:
                return result
        
            result = {
                "Driving License Number": dl_number,
                "coordinates": dl_number_coordinated
            }
            return result
        except Exception as error:
            self.logger.error(f"| Driving License Number: {error}")
            return result
        
    def _extract_dates(self):
        result = {
            "Driving License Dates": "",
            "coordinates": []
            }
        try:
            date_text = ""
            date_coords = []
            date_coordinates = []

            """date pattern"""
            date_pattern = r'\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}'

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
                "Driving License Dates": date_text,
                "coordinates": date_coordinates
            }
            return result
        except Exception as error:
            self.logger.error(f"| Driving License Dates: {error}")
            return result
    
    def _extract_pincode(self):
        result = {
            "Driving License Pincode": "",
            "coordinates": []
            }
        try:
            pincode_number = ""
            pincode_coordinates = []
            pincode_coords = []

            """get the coordinates"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if len(text) in (6,7) and text[:6].isdigit():
                    pincode_coords.append([x1, y1, x2, y2])
                    pincode_number += " "+text
                    break
            if not pincode_coords:
                return result
            
            for i in pincode_coords:
                width = i[2] - i[0]
                pincode_coordinates.append([i[0], i[1], i[0] + int(0.30 * width), i[3]])
        
            result = {
                "Driving License Pincode": pincode_number,
                "coordinates": pincode_coordinates
            }
            return result
        except Exception as error:
            self.logger.error(f"| Driving License Pincode: {error}")
            return result
    
    def _extract_places(self):
        result = {
            "Driving License Place": "",
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
                        state_name = text
                        break
            if not state_coordinates:
                return result
            
            result = {
                "Driving License Place": state_name,
                "coordinates": state_coordinates
            }
            return result
        except Exception as error:
            self.logger.error(f"| Driving License Place: {error}")
            return result

    def _extract_name(self):
        result = {
            "Driving License Name": "",
            "coordinates": []
            }
        try:
            name_text = ""
            name_coords = []
            matching_text = r"\b(?:name)\b"
            matching_text_index = None
            """get matching text index"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if re.search(matching_text, text.lower(), flags=re.IGNORECASE):
                    matching_text_index = i
                    break
        
            if matching_text_index is None:
                return result

            """get the coordinates"""
            for i in range(matching_text_index + 1, len(self.coordinates)):
                text = self.coordinates[i][4]
                if text.lower() in ['s/dmw', 'dmw', 's/', 'union', 'of', 'india',"date","birth", '“on/Daughter/Wife', "wife", "son"]:
                    break
                name_coords.append([self.coordinates[i][0], self.coordinates[i][1], self.coordinates[i][2], self.coordinates[i][3] ])
                name_text += " "+text
        
            if len(name_coords) > 1:
                result = {
                    "Driving License Name": name_text,
                    "coordinates": [[name_coords[0][0], name_coords[0][1], name_coords[-1][2], name_coords[-1][3]]]
                }
            else:
                result = {
                    "Driving License Name": name_text,
                    "coordinates": [[name_coords[0][0], name_coords[0][1], name_coords[0][2], name_coords[0][3]]]
                }
            return result
        except Exception as error:
            self.logger.error(f"| Driving License Name: {error}")
            return result

    def _extract_sdw_name(self):
        result = {
            "Driving License SDW Name": "",
            "coordinates": []
        }
        try:
            matching_text = r"\b(?:son|daughter|wife)\b"
            sdw_name = ""
            sdw_name_coordinates = []
            matching_text_index = None

            """get matching text index"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if re.search(matching_text, text.lower(), flags=re.IGNORECASE):
                    matching_text_index = i
                    break
            if matching_text_index is None:
                return result
            
            
            """get the coordinates"""
            for i in range(matching_text_index + 1, len(self.coordinates)):
                text = self.coordinates[i][4]
                if text.isupper() and text.isalpha():
                    sdw_name_coordinates.append([self.coordinates[i][0], self.coordinates[i][1], self.coordinates[i][2], self.coordinates[i][3] ])
                    sdw_name += " "+text
                    break

            if not sdw_name_coordinates:
                return result
            
            if len(sdw_name_coordinates) > 1:
                result = {
                    "Driving License SDW Name": sdw_name,
                    "coordinates": [[sdw_name_coordinates[0][0], sdw_name_coordinates[0][1], sdw_name_coordinates[-1][2], sdw_name_coordinates[-1][3]]]
                }
            else:
                result = {
                    "Driving License SDW Name": sdw_name,
                    "coordinates": [[sdw_name_coordinates[0][0], sdw_name_coordinates[0][1], sdw_name_coordinates[0][2], sdw_name_coordinates[0][3]]]
                }
            return result
        except Exception as e:
            self.logger.error(f"| Driving License SDW Name: {e} ")
            return result

    def _extract_qrcode(self):
        result = {
            "Driving License QR Code": "",
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
                "Driving License QR Code": f"Found {len(qrcode_coordinates)} QR Codes",
                "coordinates": qrcode_coordinates
            }
            return result
        except Exception as e:
            self.logger.error(f"Driving License QR Code: {e}")
            return result

    def collect_dl_doc_info(self):
        dl_card_info_list = []

        try:
            if self.DOCUMENT_REDACTION_LEVEL == 1:

                """Collect DL Number"""
                dl_number = self._extract_dl_number()
                dl_card_info_list.append(dl_number)

                """Collect DL Dates"""
                dl_dates = self._extract_dates()
                dl_card_info_list.append(dl_dates)

                """Collect DL Pincodes"""
                pincode = self._extract_pincode()
                dl_card_info_list.append(pincode)

                """Collect DL Places"""
                places = self._extract_places()
                dl_card_info_list.append(places)

                """Collect DL Name"""
                dl_name = self._extract_name()
                dl_card_info_list.append(dl_name)

                """Collect SDW Name"""
                dl_sdw_name = self._extract_sdw_name()
                dl_card_info_list.append(dl_sdw_name)

                """Collect QR Code"""
                dl_qrcode = self._extract_qrcode()
                dl_card_info_list.append(dl_qrcode)

                """Check if all the dictionaries in the list are empty"""
                all_keys_and_coordinates_empty =  all(all(not v for v in d.values()) for d in dl_card_info_list)
                if all_keys_and_coordinates_empty:
                    self.logger.error(f"| Unable to extract Driving License document information")
                    return {"message": "Unable to extract Driving License document information", "status": "REJECTED"}
                else:
                    self.logger.info(f"| Successfully Redacted Driving License Document")
                    return {"message": "Successfully Redacted Driving License Document", "status": "REDACTED", "data": dl_card_info_list}
            else:

                """Collect DL Number"""
                dl_number = self._extract_dl_number()
                if len(dl_number['coordinates']) == 0:
                    self.logger.error("| Driving license number not found")
                    return {"message": "Unable to extract driving license number", "status": "REJECTED"}
                dl_card_info_list.append(dl_number)

                """Collect DL Dates"""
                dl_dates = self._extract_dates()
                if len(dl_dates['coordinates']) == 0:
                    self.logger.error("| Driving license dates not found")
                    return {"message": "Unable to extract dates from license number", "status": "REJECTED"}
                dl_card_info_list.append(dl_dates)

                """Collect DL Pincodes"""
                pincode = self._extract_pincode()
                dl_card_info_list.append(pincode)

                """Collect DL Places"""
                places = self._extract_places()
                dl_card_info_list.append(places)

                """Collect DL Name"""
                dl_name = self._extract_name()
                if len(dl_name['coordinates']) == 0:
                    self.logger.error("| Driving license name not found")
                    return {"message": "Unable to extract name from driving license", "status": "REJECTED"}
                dl_card_info_list.append(dl_name)

                """Collect SDW Name"""
                dl_sdw_name = self._extract_sdw_name()
                if len(dl_sdw_name['coordinates']) == 0:
                    self.logger.error("| Driving license SDW name not found")
                    return {"message": "Unable to extract SDW name from driving license", "status": "REJECTED"}
                dl_card_info_list.append(dl_sdw_name)

                """Collect QR Code"""
                dl_qrcode = self._extract_qrcode()
                if len(dl_qrcode['coordinates']) == 0:
                    self.logger.error("| Driving license QR Code not found")
                else:
                    dl_card_info_list.append(dl_qrcode)

                self.logger.info(f"| Successfully Redacted Driving License Document")
                return {"message": "Successfully Redacted Driving License Document", "status": "REDACTED", "data": dl_card_info_list}

        except Exception as e:
            self.logger.error(f"| Collecting Driving License document information: {e}")
            return {"message": "Error collecting Driving License document information", "status": "REJECTED"}