import re

class CleanText:
    def __init__(self, text: str) -> None:
        self.text = text
    
    def clean_text(self) -> list:
        # Check if self.text is a dictionary and contains the key "text"
        if not isinstance(self.text, dict) or "text" not in self.text:
            raise ValueError("Invalid input. Expected a dictionary with key 'text'.")

        # Retrieve the text to clean
        text_to_clean = self.text["text"]

        # Replace non-alphanumeric characters with spaces
        clean_data = re.sub(r'[^a-zA-Z0-9\s:/-]', ' ', text_to_clean)

        # Split the text into lines and clean each line
        clean_lines = [line.strip() for line in clean_data.split('\n') if line.strip()]

        return clean_lines
