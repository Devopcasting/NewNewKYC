import re
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging

class PancardPattern2:
    def __init__(self, text_coordinates, data_text, label: str) -> None:
        self.text_coordinates = text_coordinates
        self.data_text = data_text
        self._setup_logging()

        if label == "User":
            self.SET_LABEL = "Pancard Username"
        else:
            self.SET_LABEL = "Pancard Father's Name"

    def _setup_logging(self):
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()
    
    def extract_username_p2(self) -> dict:
        result = {
            f"{self.SET_LABEL}": "",
            "coordinates": []
        }
        try:
            pancard_name_text = ""
            pancard_name_coordinates = []
            matching_text_keyword = ['GOVTOF INDE','fETAX DEPARTMEN','fETAX','GoyT  OF UNPIA', 'OF INDIA', "GOVT. OF INDIA"," GOVT.", "INDIA", "INCOME", "TAX", "DEPARTMENT", "DEPARTNENT", "INCOME TAX DEPARTNENT"]

            """Generate list of text"""
            split_text_list = [i for i in self.data_text.splitlines() if len(i) != 0]
    
            """Get the matching keyword index"""
            matching_text_index = self.__find_matching_text_index_username(split_text_list, matching_text_keyword)
            if matching_text_index == 404:
                return result
            """
                - Get the next line of matching index
                - Regex match only alpha
            """
            next_line_list = []
            pattern = r"\b(?:department|a|govtof|inde|goyt|departmen|fetax|departnent|income|sires|account|card|tax|govt|are|ed|ah|if|vin|an|ad|z|of india)\b(?=\s|\W|$)|[-=\d]+"
            for line in split_text_list[matching_text_index:]:
                match = re.search(pattern, line.lower(), flags=re.IGNORECASE)
                if match:
                    continue
                has_uppercase = lambda text: any(word.isupper() for word in text.split())
                if has_uppercase(line):
                    next_line_list = line.split()
                    next_line_list = [word for word in next_line_list if word.isupper()]
                    break
            if not next_line_list:
                return result
            
            """Remove specail characters"""
            clean_next_line = [element for element in next_line_list if re.search(r'[a-zA-Z0-9]', element)]
            pancard_name_text = " ".join(clean_next_line)

            """Get the coordinates"""
            if len(clean_next_line) > 1:
                clean_next_line = clean_next_line[:-1]
            
            for i,(x1,y1,x2,y2,text) in enumerate(self.text_coordinates):
                if text in clean_next_line:
                    pancard_name_coordinates.append([x1, y1, x2, y2])
                if len(pancard_name_coordinates) == len(clean_next_line):
                    break
            if not pancard_name_coordinates:
                return result
            
            if len(next_line_list) > 1:
                result = {
                    f"{self.SET_LABEL}": pancard_name_text,
                    "coordinates": [[
                        pancard_name_coordinates[0][0],
                        pancard_name_coordinates[0][1],
                        pancard_name_coordinates[-1][2],
                        pancard_name_coordinates[-1][3],
                        ]]
                }
            else:
                result = {
                    f"{self.SET_LABEL}": pancard_name_text,
                    "coordinates": [[
                        pancard_name_coordinates[0][0],
                        pancard_name_coordinates[0][1],
                        pancard_name_coordinates[0][2],
                        pancard_name_coordinates[0][3],
                        ]]
                }
            return result
        except Exception as e:
            self.logger.error(f"| {self.SET_LABEL}: {e}")
            return result

    def extract_father_name_p2(self) -> dict:
        result = {
            f"{self.SET_LABEL}": "",
            "coordinates": []
        }
        try:
            pancard_name_text = ""
            pancard_name_coordinates = []
            matching_text_index = None
            matching_text_list = []

            """Generate list of text"""
            split_text_list = [i for i in self.data_text.splitlines() if len(i) != 0]

            """Create Reverse list"""
            reverse_line_list = split_text_list[::-1]
            print(reverse_line_list)

            """Matching patterns"""
            date_pattern = r'\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}'
            matching_pattern = r"bonn|birth"

            for i, text in enumerate(reverse_line_list):
                match_dob = re.search(date_pattern, text)
                match_pattern = re.search(matching_pattern, text, flags=re.IGNORECASE)
                if match_dob or match_pattern:
                    if len(reverse_line_list[i + 1]) == 1:
                        matching_text_index = i + 2
                        break
                    else:
                        matching_text_index = i + 1
                        break
            if matching_text_index is None:
                return result
            
            """Get the coordinates"""
            for text in reverse_line_list[matching_text_index :]:
                if text.isupper():
                    pancard_name_text += " "+ text
                    matching_text_list = text.split()
                    break
            if not matching_text_list:
                return result
            
            if len(matching_text_list) > 1:
                matching_text_list = matching_text_list[:-1]
            
            for i,(x1, y1, x2, y2, text) in enumerate(self.text_coordinates):
                if text in matching_text_list:
                    pancard_name_coordinates.append([x1, y1, x2, y2])
                if len(matching_text_list) == len(pancard_name_coordinates):
                    break
                
            if len(pancard_name_coordinates) > 1:
                result = {
                    f"{self.SET_LABEL}": pancard_name_text,
                    "coordinates": [[pancard_name_coordinates[0][0], pancard_name_coordinates[0][1], pancard_name_coordinates[-1][2], pancard_name_coordinates[-1][3]]]
                }
            else:
                result = {
                    f"{self.SET_LABEL}": pancard_name_text,
                    "coordinates": [[pancard_name_coordinates[0][0], pancard_name_coordinates[0][1], pancard_name_coordinates[0][2], pancard_name_coordinates[0][3]]]
                }
            return result
        except Exception as e:
            self.logger.error(f"| {self.SET_LABEL}: {e}")
            return result

    def __find_matching_text_index_username(self, lines: list, matching_text: list) -> int:
        for i,line in enumerate(lines):
            for k in matching_text:
                if k in line:
                    return i
        return 404