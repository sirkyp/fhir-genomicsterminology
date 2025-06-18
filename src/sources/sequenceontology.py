from pathlib import Path
import json
import utils.utils as utils

from fhir.resources.codesystem import CodeSystem, CodeSystemConcept, CodeSystemProperty

SOURCE_DATA_FILE_URL = "https://raw.githubusercontent.com/The-Sequence-Ontology/SO-Ontologies/refs/heads/master/Ontology_Files/so-simple.json"
SOURCE_CODESYSTEM_URL = "https://terminology.hl7.org/CodeSystem-SO.json"
LOCAL_DATA_DIR = Path("./data/so")
LOCAL_DATA_FILE = LOCAL_DATA_DIR / "source_data.json"
LOCAL_CODESYSTEM_FILE = LOCAL_DATA_DIR / "codesystem.json"

class SequenceOntology:
    def __init__(self):
        """
        Initialize the SequenceOntology class.
        """
        # Ensure the data directory exists
        LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)

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
    
        if not LOCAL_DATA_FILE.exists():
            print(f"{LOCAL_DATA_FILE} data file does not exist.")
            return

        print(f"Creating FHIR CodeSystem for Sequence Ontology from {SOURCE_CODESYSTEM_URL}...")        
        soCS = utils.new_CodeSystemFromURL(url=SOURCE_CODESYSTEM_URL)
        # Add properties specific to Sequence Ontology
        soCS.property = [CodeSystemProperty(
            code="comments",
            type='string',
            description="Comments about the concept")]

        print(f"Processing data from {LOCAL_DATA_FILE}...")
        data = {}
        with LOCAL_DATA_FILE.open('r') as file:
            data = json.load(file)

        for graph in data['graphs']:
            for node in graph['nodes']:
                node_id = node.get('id', '').split('/')[-1] if node.get('id') else ''
                node_label = node.get('lbl', '')
                node_def = node.get('meta', {}).get('definition', {}).get('val', '')
                c = utils.new_CodeSystemConcept(system=soCS, code=node_id, display=node_label, definition=node_def)
                if c is not None:
                    # Add properties to the concept
                    # need special logic to handle comments
                    values = node.get('meta', {}).get('comments', [])
                    combined_value = '|'.join(values) if values else ''
                    utils.new_CodeSystemConceptProperty(concept=c, code='comments', type='string', value=combined_value)

        # Save the processed CodeSystem to a file
        print(f"Saving processed CodeSystem to {LOCAL_CODESYSTEM_FILE}...")
        LOCAL_CODESYSTEM_FILE.write_text(soCS.model_dump_json(indent=2))
