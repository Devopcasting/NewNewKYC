import re

class IdentifyCDSLDocument:
    def __init__(self, clean_text: list) -> None:
        self.clean_text = clean_text
        """Regex expression for CDSL document identification"""
        self.cdsl_regex = r"\b(?: cdsl|ventures|kyc)\b"
    
    def check_cdsl_document(self) -> bool:
        for text in self.clean_text:
            if re.search(self.cdsl_regex, text, flags=re.IGNORECASE):
                return True
        return False