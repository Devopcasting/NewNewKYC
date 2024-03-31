import pytesseract
import cv2
from helper.clean_text import CleanText
from documents.cdsl.identify_cdsl import IdentifyCDSLDocument
from documents.pancard.identify_pancard import IdentifyPancardDocument
from documents.aadhaarcard.identify_aadhaarcard import IdentifyAadhaarCardDocument

class IdentifyDocumentType:
    def __init__(self, document_path: str) -> None:
        self.document_path = document_path
        """Clean the text from image"""
        data_text = self._get_text_from_image_doc()
        clean_data_text = CleanText(data_text).clean_text()
    
        """Initialize document identification objects"""
        self.document_identification_objects = {
            "CDSL": IdentifyCDSLDocument(clean_data_text).check_cdsl_document(),
            "PANCARD": IdentifyPancardDocument(clean_data_text).check_pancard_document(),
            "E-Aadhaar": IdentifyAadhaarCardDocument(clean_data_text).check_e_aadhaarcard_document(),
            "Aadhaar": IdentifyAadhaarCardDocument(clean_data_text).check_aadhaarcard_document()
        }
        
    def _get_text_from_image_doc(self) -> dict:
        if self._check_rgb_image():
            tesseract_config = r'-l eng --oem 3 --psm 11'
        else:
            tesseract_config = r'-l eng --oem 3 --psm 11'

        return pytesseract.image_to_string(self.document_path, output_type=pytesseract.Output.DICT, config=tesseract_config)

    def _check_rgb_image(self) -> bool:
        document = cv2.imread(self.document_path)
        if len(document.shape) < 3: return True
        if document.shape[2]  == 1: return True
        b,g,r = document[:,:,0], document[:,:,1], document[:,:,2]
        if (b==g).all() and (b==r).all(): return True
        return False
    
    def identify_document_type(self, document_type: str) -> bool:
        if document_type in self.document_identification_objects:
            return self.document_identification_objects[document_type]
        else:
            return False