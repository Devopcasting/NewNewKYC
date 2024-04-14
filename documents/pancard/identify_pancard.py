import re

class IdentifyPancardDocument:
    def __init__(self, clean_text: list) -> None:
        self.clean_text = clean_text
        """Regex expression pattern for PAN card identifiers"""
        self.pancard_regex = r"\b(?: account|permarent|pefirianent|petmancnt|petraancnt|income|tax|incometax|department|permanent|petianent|incometaxdepartment|incombtaxdepartment|pormanent|perenent|tincometaxdepakinent|fetax|departmen|NT NUMBER)\b"

    def check_pancard_document(self) -> bool:
        for text in self.clean_text:
            if re.search(self.pancard_regex, text, flags=re.IGNORECASE):
                return True
        return False