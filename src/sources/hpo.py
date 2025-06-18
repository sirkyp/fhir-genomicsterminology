from pathlib import Path
import json

import utils.utils as utils
from fhir.resources.codesystem import CodeSystem, CodeSystemConcept, CodeSystemProperty

SOURCE_DATA_FILE_URL = "https://github.com/obophenotype/human-phenotype-ontology/releases/download/v2025-05-06/hp-full.json"
SOURCE_CODESYSTEM_URL = "https://terminology.hl7.org/CodeSystem-HPO.json"
LOCAL_DATA_DIR = Path("./data/hpo")
LOCAL_DATA_FILE = LOCAL_DATA_DIR / "source_data.json"
LOCAL_CODESYSTEM_FILE = LOCAL_DATA_DIR / "codesystem.json"

class HPO:
  def __init__(self):
    """
    Initialize the HPO class.
    """
    # Ensure the data directory exists
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)

  def load_data(self):
    """
    Load data from the HPO source and save it to a file.
    """
    print("Loading HPO data...")

    if utils.is_file_fresh(LOCAL_DATA_FILE, 24):
        return

    utils.download_file(SOURCE_DATA_FILE_URL, LOCAL_DATA_FILE)

  def process_data(self):
    """
    Process the HPO data and create FHIR CodeSystem concepts.
    """
    print("Processing HPO data")
  
    if not LOCAL_DATA_FILE.exists():
      print("Data file does not exist. Please run the load_data function first.")
      return

    print(f"Creating FHIR CodeSystem for HPO from {SOURCE_CODESYSTEM_URL}...")
    hpoCS = utils.new_CodeSystemFromURL(url=SOURCE_CODESYSTEM_URL)
 
    data = {}
    print(f"Processing data from {LOCAL_DATA_FILE}...")
    with LOCAL_DATA_FILE.open('r') as file:
      data = json.load(file)

    for graph in data['graphs']:
      for node in graph['nodes']:
        node_id = node.get('id', '').split('/')[-1] if node.get('id') else ''
        node_label = node.get('lbl', '')
        node_def = node.get('meta', {}).get('definition', {}).get('val', '')
        utils.new_CodeSystemConcept(system=hpoCS, code=node_id, display=node_label, definition=node_def)

    # Save the processed CodeSystem to a file
    print(f"Saving processed CodeSystem to {LOCAL_CODESYSTEM_FILE}...")
    LOCAL_CODESYSTEM_FILE.write_text(hpoCS.model_dump_json(indent=2))
