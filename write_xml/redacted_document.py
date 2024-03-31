import os
import re
import xml.etree.ElementTree as ET

class WriteRedactedDocumentXML:
    def __init__(self, result_path: str, original_document_name: str, result_data: list ) -> None:
        self.xml_path = result_path
        self.xml_file_name = original_document_name
        self.result_data = result_data

    def writexml(self):
        """Set XML file path"""
        xml_file_path = os.path.join(self.xml_path, self.xml_file_name.split('.')[0]+'.xml')
        if os.path.exists(xml_file_path):
            os.remove(xml_file_path)
        
        """
            Prepare Data 
            - Frame-ID
            - Document ID
        """
        pattern = "^[0-9]+F[0-9a-fA-Z_-]+"
        frame_str = self.xml_file_name.split('.')[0].split('-')[0]
        matched_str = re.match(pattern, self.xml_file_name)
        frame_id = 0

        if matched_str:
            frame_id = int(frame_str.split('F')[0]) - 1
            document_id = re.split('_', self.xml_file_name)[0].split('-')[1][:-1]
        else:
            doc_id_num = re.split('_', self.xml_file_name)[0]
            document_id = doc_id_num[:-1]
        
        """Prepare XML Data"""
        xml_data = []
        count_index = 1
        coordinates_list = []
        for i in self.result_data:
            k_list = i['coordinates']
            for j in k_list:
                if len(j) != 0:
                    coordinates_list.append(j)

        for i in coordinates_list:
            x1, y1, x2, y2 = i
            xml_data.append(f'0,0,0,,,,0,0,0,0,0,0,,vv,CVDPS,vv,{frame_id},{document_id},0,{count_index},{x1},{y1},{x2},{y2},0,0,')
            x1, y1, x2, y2 = [0, 0, 0, 0]
            count_index = count_index + 1
        
        """Create the root element"""
        root = ET.Element("DataBase")

        """Add count element"""
        count = ET.SubElement(root, "Count")
        count.text = f'{len(xml_data)}'

        """Create the DatabaseRedactions element"""
        database_redactions = ET.SubElement(root, "DatabaseRedactions")

        """Create DatabaseRedaction elements in a loop"""
        for i, item in enumerate(xml_data, start=1):
            database_redaction = ET.SubElement(database_redactions, "DatabaseRedaction", ID=str(i))
            database_redaction.text = item
        
        """Create an ElementTree object"""
        tree = ET.ElementTree(root)

        """Write the XML to a file"""
        tree.write(xml_file_path , encoding="utf-8", xml_declaration=True)
    
    def write_redacted_data_xml(self):
        """Set XML file path"""
        redacted_text_xml_name = self._rename_xml_file(self.xml_file_name)
        xml_file_path = os.path.join(self.xml_path, redacted_text_xml_name)
        if os.path.exists(xml_file_path):
            os.remove(xml_file_path)
        """
            Prepare Data 
            - Frame-ID
            - Document ID
        """
        pattern = "^[0-9]+F[0-9a-fA-Z_-]+"
        frame_str = self.xml_file_name.split('.')[0].split('-')[0]
        matched_str = re.match(pattern, self.xml_file_name)
        frame_id = 0

        if matched_str:
            frame_id = int(frame_str.split('F')[0]) - 1
            document_id = re.split('_', self.xml_file_name)[0].split('-')[1][:-1]
        else:
            doc_id_num = re.split('_', self.xml_file_name)[0]
            document_id = doc_id_num[:-1]
        
        """Prepare XML data"""
        xml_data = []
        count_index = 1
        for i in self.result_data:
            title_text = list(i.keys())[0]
            value_text = i[title_text]
            xml_data.append(f'"Title": "{title_text}", "FrameID": "{frame_id}", "DocID": "{document_id}", "Value": "{value_text}"')
            count_index = count_index + 1

        """Create the root element"""
        root = ET.Element("DataBase")

        """Add count element"""
        count = ET.SubElement(root, "Count")
        count.text = f'{len(xml_data)}'

        """Create the DatabaseRedactions element"""
        database_redactions = ET.SubElement(root, "indexvalues")

        """Create DatabaseRedaction elements in a loop"""
        for i, item in enumerate(xml_data, start=1):
            database_redaction = ET.SubElement(database_redactions, "indexvalue", ID=str(i))
            database_redaction.text = item
        
        """Create an ElementTree object"""
        tree = ET.ElementTree(root)

        """Write the XML to a file"""
        tree.write(xml_file_path , encoding="utf-8", xml_declaration=True)

    def _rename_xml_file(self, filename: str) -> str:
        filename_list = filename.split('_', 1)
        new_filename = f"{filename_list[0]}-RD_{filename_list[-1]}"
        new_filename = new_filename.rsplit('.', 1)[0] + '.xml'
        return new_filename





        







