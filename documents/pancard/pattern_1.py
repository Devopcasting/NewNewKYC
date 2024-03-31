import re
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging

class PancardPattern1:
    def __init__(self, text_coordinates, data_text, keywords: list, label: str) -> None:
        self.text_coordinates = text_coordinates
        self.data_text = data_text
        self.keywords = keywords
        self._setup_logging()

        if label == "User":
            self.SET_LABEL = "Pancard Username"
        else:
            self.SET_LABEL = "Pancard Father's Name"

    def _setup_logging(self):
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()
        
    def extract_user_father_name(self) -> dict:
        result = {
            f"{self.SET_LABEL}": "",
            "coordinates": []
        }
        try:
            pancard_name_text = ""
            pancard_name_coordinates = []
            matching_text_index = None

            """Generate list of text"""
            split_text_list = [i for i in self.data_text.splitlines() if len(i) != 0]
            
            """Get the matching keyword index"""
            matching_text_index = self._find_matching_keyword_index(split_text_list, self.keywords)
            if matching_text_index == 404:
                return result
            """
                - Get the next line of matching index
                - Regex match only alpha
            """
            next_line_list = []
            for text in split_text_list[matching_text_index + 1:]:
                if text.isupper():
                     next_line_list = text.split()
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

    def _find_matching_keyword_index(self, lines: list, keyword_text: list) -> int:
        matching_pattern = r"(?:" + "|".join(re.escape(word) for word in keyword_text) + r")"
        for i, line in enumerate(lines):
            if re.search(matching_pattern, line, flags=re.IGNORECASE):
                return i
        return 404

    def _has_special_characters(self, name: str):
        special_char_pattern = re.compile(r'[@_#$%^&()<>?/\|}{~]')
        if special_char_pattern.search(name) is not None:
            return True
        else:
            return False

