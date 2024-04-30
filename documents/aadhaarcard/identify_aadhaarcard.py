import re

class IdentifyAadhaarCardDocument:
    def __init__(self, clean_text: list) -> None:
        self.clean_text = clean_text
        print(self.clean_text)
        # Regular expression pattern for Aadhaar card identifiers
        self.aadhaarcard_regex = r"\b(?:enrollment|enrolment|enrollmentno|Enrotiment|enrotimant|UniqualidentificationsAuthority|Unique identification Authority oF india|enroliment|/enrolment|male|female|help@uidal.gov.in|government|government of india|www.uidal.gov.in|unique identification authority of india|aadhaar| autiority of india)\b"
       
        # Regular expression pattern for E-Aadhaar card identifiers
        self.eaadhaarcard_regex = r"\b(?:enrollment|enrolment|enroliment|enrolment|enrotiment|/enrolment|enrotimant|enrallment|evavenrolment|eivavenrolment|ehyollment|enrollmentno|This ts electronica ly generated letter|Aadhaar is valid throughout the country)\b"

        # Regular expression pattern for Aadhaar card identifiers
        self.aadhaar_card_regex = r"\b(?:uidal.gov.in|male|female|femala|eemale|government of india|UniqualidentificationsAuthority|Unique identification Authority oF india|Aadhaar-Aam Admi ka Adhikar|autiority of india)\b"

    def check_aadhaar_card_format(self) -> bool:
        for text in self.clean_text:
            if re.search(self.aadhaarcard_regex, text, flags=re.IGNORECASE):
                return True
        return False

    def check_aadhaarcard_document(self) -> bool:
        for text in self.clean_text:
            if re.search(self.aadhaar_card_regex, text, flags=re.IGNORECASE):
                return True
        return False


    def check_e_aadhaarcard_document(self):
        for text in self.clean_text:
            if re.search(self.eaadhaarcard_regex, text, flags=re.IGNORECASE):
                return True
        return False