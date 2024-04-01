import re

class IdentifyDrivingLicenseDocument:
    def __init__(self, clean_text: list) -> None:
        self.clean_text = clean_text
        # Regular expression pattern for DL card identifiers
        self.dl_regex = r"\b(?:union|driving|motor)\b"

    def check_dl_document(self) -> bool:
        for text in self.clean_text:
            if re.search(self.dl_regex, text, flags=re.IGNORECASE):
                return True
        return False