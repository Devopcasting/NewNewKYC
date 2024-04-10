import os
import re
import xml.etree.ElementTree as ET
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging

class WriteRedactedDocumentXML:
    def __init__(self, result_path: str, original_document_name: str, result_data: list ) -> None:
        self.xml_path = result_path
        self.xml_file_name = original_document_name
        self.result_data = result_data
        self._setup_logging()

    def _setup_logging(self):
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()
    
    def _parse_document_info(self):
        try:
            pattern = "^[0-9]+F[0-9a-fA-Z_-]+"
            frame_str = self.xml_file_name.split('.')[0].split('-')[0]
            matched_str = re.match(pattern, self.xml_file_name)

            if matched_str:
                frame_id = int(frame_str.split('F')[0]) - 1
                document_id = re.split('_', self.xml_file_name)[0].split('-')[1][:-1]
            else:
                doc_id_num = re.split('_', self.xml_file_name)[0]
                frame_id = 0
                document_id = doc_id_num[:-1]
            return frame_id, document_id
        except Exception as e:
            self.logger.error(f"| Parsing redacted document info: {e}")

    def _prepare_coordinates_xml_data(self, frame_id, document_id):
        xml_data = []
        count_index = 1
        coordinates_list = [j for i in self.result_data for j in i['coordinates'] if len(j) != 0]

        for x1, y1, x2, y2 in coordinates_list:
            xml_data.append(f'0,0,0,,,,0,0,0,0,0,0,,vv,CVDPS,vv,{frame_id},{document_id},0,{count_index},{x1},{y1},{x2},{y2},0,0')
            count_index += 1

        return xml_data

    def _prepare_text_xml_data(self, frame_id, document_id):
        xml_data = []
        for i in self.result_data:
            title_text, value_text = list(i.items())[0]
            xml_data.append(f'"Title": "{title_text}", "FrameID": "{frame_id}", "DocID": "{document_id}", "Value": "{value_text}"')
        return xml_data

    def _write_xml(self, xml_data, element_name):
        root = ET.Element("DataBase")
        count = ET.SubElement(root, "Count")
        count.text = str(len(xml_data))
        database_element = ET.SubElement(root, element_name)

        for i, item in enumerate(xml_data, start=1):
            sub_element = ET.SubElement(database_element, element_name[:-1], ID=str(i))
            sub_element.text = str(item)

        xml_file_path = os.path.join(self.xml_path, self._rename_xml_file(self.xml_file_name, element_name))
        tree = ET.ElementTree(root)
        tree.write(xml_file_path , encoding="utf-8", xml_declaration=True)

    def write_xml(self):
        try:
            self.logger.info(f"| Writing Redacted Coordinates in XML: {self.xml_file_name}")
            frame_id, document_id = self._parse_document_info()
            coordinates_xml_data = self._prepare_coordinates_xml_data(frame_id, document_id)
            self._write_xml(coordinates_xml_data, "DatabaseRedactions")
            return True
        except Exception as e:
            self.logger.error(f"| Writing Redacted Coordinates XML: {e}")
            return False

    def write_redacted_data_xml(self):
        try:
            self.logger.info(f"| Writing Redacted Text in XML: {self.xml_file_name}")
            frame_id, document_id = self._parse_document_info()
            text_xml_data = self._prepare_text_xml_data(frame_id, document_id)
            self._write_xml(text_xml_data, "indexvalues")
            return True
        except Exception as e:
            self.logger.error(f"| Writing Redacted Text XML: {e}")
            return False

    @staticmethod
    def _rename_xml_file(filename: str, element_name: str) -> str:
        filename_list = filename.split('_', 1)
        if element_name == "indexvalues":
            new_filename = f"{filename_list[0]}-RD_{filename_list[-1]}"
        else:
            new_filename = filename

        return new_filename.rsplit('.', 1)[0] + '.xml'
