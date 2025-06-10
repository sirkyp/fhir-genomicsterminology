import os
import json

import utils.utils as utils
from fhir.codesystem import FHIRCodeSystem

SOURCE_DATA_FILE_URL = "https://raw.githubusercontent.com/The-Sequence-Ontology/SO-Ontologies/refs/heads/master/Ontology_Files/so-simple.json"
SOURCE_CODESYSTEM_URL = "https://terminology.hl7.org/CodeSystem-SO.json"
LOCAL_DATA_DIR = "./data/so"
LOCAL_DATA_FILE = f"{LOCAL_DATA_DIR}/source_data.json"
LOCAL_CODESYSTEM_FILE = f"{LOCAL_DATA_DIR}/codesystem.json"

class SequenceOntology:
    def __init__(self):
        """
        Initialize the SequenceOntology class.
        """
        # Ensure the data directory exists
        os.makedirs(LOCAL_DATA_DIR, exist_ok=True)

    def load_data(self):
        """
        Load data from the Sequence Ontology source and save it to a file.
        """
        print("Loading Sequence Ontology data...")
        
        # Check if the data file already exists
        if utils.is_file_fresh(LOCAL_DATA_FILE, 24):
            return

        utils.download_file(SOURCE_DATA_FILE_URL, LOCAL_DATA_FILE)

    def process_data(self):
        """
        Process the Sequence Ontology data and create FHIR CodeSystem concepts.
        """
        print("Processing Sequence Ontology data...")
    
        if not os.path.exists(LOCAL_DATA_FILE):
            print(f"{LOCAL_DATA_FILE} data file does not exist.")
            return

        print(f"Creating FHIR CodeSystem for Sequence Ontology from {SOURCE_CODESYSTEM_URL}...")        
        soCS = FHIRCodeSystem()
        soCS.fetch_cs(url=SOURCE_CODESYSTEM_URL)
        # Add properties specific to Sequence Ontology
        # Note: You may need to adjust these properties based on your SO data structure
        soCS.add_property(code="comments", type=FHIRCodeSystem.PropertyType.STRING, description="Comments about the concept")
 
        print(f"Processing data from {LOCAL_DATA_FILE}...")
        data = {}
        with open(LOCAL_DATA_FILE, 'r') as file:
            data = json.load(file)

        for graph in data['graphs']:
            for node in graph['nodes']:
                node_id = node.get('id', '').split('/')[-1] if node.get('id') else ''
                node_label = node.get('lbl', '')
                node_def = node.get('meta', {}).get('definition', {}).get('val', '')
                c = soCS.add_concept(code=node_id, display=node_label, definition=node_def)

                # Add properties to the concept
                # need special logic to handle comments
                values = node.get('meta', {}).get('comments', [])
                combined_value = '|'.join(values) if values else ''
                c.add_property(code='comments', value=combined_value, type=FHIRCodeSystem.PropertyType.STRING)

        with open(LOCAL_CODESYSTEM_FILE, 'w') as file:
            # Save the processed CodeSystem to a file
            print(f"Saving processed CodeSystem to {LOCAL_CODESYSTEM_FILE}...")
            file.write(soCS.to_json())
