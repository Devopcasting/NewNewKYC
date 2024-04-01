import pytesseract
import re

class TextCoordinates:
    def __init__(self, image_path) -> None:
        self.image_path = image_path
        
    
    # func: generate coordinates
    def generate_text_coordinates(self) -> list:
        tesseract_config = r'--oem 3 --psm 11'
        data = pytesseract.image_to_data(self.image_path, output_type=pytesseract.Output.DICT, config=tesseract_config)
        special_characters = r'[!@#$%^&*()_\-+{}\[\]:;,.?~\\|]'
    
        coordinates = []

        for i in range(len(data['text'])):
            text = data['text'][i]
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            # Filter out empty strings and  special characters
            if not re.search(special_characters, text) and len(text) != 0:
                coordinates.append((x,y,x + w, y + h, text))
        return coordinates