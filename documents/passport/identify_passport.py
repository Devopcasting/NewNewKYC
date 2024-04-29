import re

class IdentifyPassportDocument:
    def __init__(self, clean_text: list) -> None:
        self.clean_text = clean_text
        #print(self.clean_text)
        # Regular expression pattern for Passport identifiers
        #self.passport_regex = r"\b(?:republic|pusepart|jpassport|passport|passpon|ipassport|overseas|citizen|bissport|passoars|passportno|paeupari)\b"
        self.passport_regex = r"(?:republic|posspau|pusepart|passgert|jpassport|pasaport|passport|passpon|ipassport|overseas|citizen|bissport|passoars|passportno|paeupari|paasport| given name| given neme)"

    def check_passport_document(self) -> bool:
        for text in self.clean_text:
            if re.search(self.passport_regex, text, flags=re.IGNORECASE):
                return True
        return False