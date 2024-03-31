import re

class IdentifyEPanCardDocument:
    def __init__(self, clean_text: list) -> None:
        self.clean_text = clean_text
        """Regex expression pattern for E-PAN card identifiers"""
        self.pancard_regex = r"\b(?: e-pan)\b"

    def check_e_pancard_document(self) -> bool:
        for text in self.clean_text:
            if re.search(self.pancard_regex, text, flags=re.IGNORECASE):
                return True
        return False
    