import os
import re
import xml.etree.ElementTree as ET
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging

class WriteRejectedDocumentXML:
    def __init__(self, redacted_path: str, original_document_name: str, ocr_obj_info: list) -> None:
        self.xml_path = redacted_path
        self.xml_file_name = original_document_name
        self.content = ocr_obj_info
        self._setup_logging()

    def _setup_logging(self):
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()
    
    def _extract_ids(self) -> tuple:
        try:
            # Extract frame ID and document ID from the file name
            pattern = "^[0-9]+F[0-9a-fA-Z_-]+"
            frame_str = self.xml_file_name.split('.')[0].split('-')[0]
            matched_str = re.match(pattern, self.xml_file_name)
            if matched_str:
                frame_id = int(frame_str.split('F')[0]) - 1
                doc_id = re.split('_', self.xml_file_name)[0].split('-')[1][:-1]
            else:
                doc_id_num = re.split('_', self.xml_file_name)[0]
                doc_id = doc_id_num[:-1]
                frame_id = 0
            return frame_id, doc_id
        except Exception as e:
            self.logger.error(f"| Parsing rejected document info: {e}")

    def _prepare_data(self) -> list:
        # Prepare data for XML
        data = []
        count_index = 1
        for coords in self.content:
            x1, y1, x2, y2 = coords
            data.append(f'0,0,0,,,,0,0,0,0,0,0,,vv,CVDPS,vv,{self.frame_id},{self.doc_id},0,{count_index},{x1},{y1},{x2},{y2},0,0')
            count_index += 1
        return data

    def _create_xml_structure(self, data: list) -> ET.Element:
        # Create XML structure
        root = ET.Element("DataBase")
        count = ET.SubElement(root, "Count")
        count.text = str(len(data))
        database_redactions = ET.SubElement(root, "DatabaseRedactions")
        for i, item in enumerate(data, start=1):
            database_redaction = ET.SubElement(database_redactions, "DatabaseRedaction", ID=str(i))
            database_redaction.text = item
        return root

    def writexml(self) -> bool:
        # Extract IDs
        self.frame_id, self.doc_id = self._extract_ids()

        # Prepare data
        data = self._prepare_data()

        # Create XML structure
        root = self._create_xml_structure(data)
        tree = ET.ElementTree(root)

        # Write XML to file
        xml_file_path = os.path.join(self.xml_path, f"{self.xml_file_name.split('.')[0]}.xml")
        if os.path.exists(xml_file_path):
            os.remove(xml_file_path)
        tree.write(xml_file_path, encoding="utf-8", xml_declaration=True)

        """Create Empty file for REJECTED doc"""
        filename_list = self.xml_file_name.split('_', 1)
        new_filename = f"{filename_list[0]}-RJ_{filename_list[-1]}"
        new_filename = new_filename.rsplit('.', 1)[0] + '.xml'
        rejected_doc_file_path = os.path.join(self.xml_path, new_filename)
        with open(rejected_doc_file_path, "w"):
            pass
        
        return True
