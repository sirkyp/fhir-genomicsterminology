import requests
import os
import json
import utils.utils as utils
from fhir.resources.codesystem import CodeSystem, CodeSystemConcept, CodeSystemProperty

# Configuration settings
SOURCE_DATA_API_URL = "https://www.pharmvar.org/api-service/alleles?exclude-sub-alleles=false&include-reference-variants=true&include-retired-alleles=false&include-retired-reference-sequences=false"
SOURCE_CODESYSTEM_URL = 'https://terminology.hl7.org/CodeSystem-PharmVar.json'
LOCAL_DATA_DIR = "./data/pharmvar"
LOCAL_DATA_FILE = f"{LOCAL_DATA_DIR}/source_data.json"
LOCAL_CODESYSTEM_FILE = f"{LOCAL_DATA_DIR}/codesystem.json"

class PharmVar:
    def __init__(self):
        # Ensure the data directory exists
        os.makedirs(LOCAL_DATA_DIR, exist_ok=True)

    def load_data(self):
        """
        Load data from the PharmVar API and save it to a file.
        """
        # Check if the data file already exists
        if utils.is_file_fresh(LOCAL_DATA_FILE):
            return

        utils.download_file(SOURCE_DATA_API_URL, LOCAL_DATA_FILE)

    def process_data(self):
        """
        Process the PharmVar data and create FHIR CodeSystem concepts.
        """
        print("Processing PharmVar data...")
        if not os.path.exists(LOCAL_DATA_FILE):
            print(f"{LOCAL_DATA_FILE} data file does not exist.")
            return

        print(f"Loading CodeSystem data from {SOURCE_CODESYSTEM_URL}...")
        pvCS = utils.new_CodeSystemFromURL(url=SOURCE_CODESYSTEM_URL)
        
        pvCS.content = 'complete'

        pvCS.property = [
            CodeSystemProperty(
            code="geneSymbol",
            description="Gene Symbol",
            type='string'
            ),
            CodeSystemProperty(
            code="function", 
            description="Function",
            type='string'
            ),
            CodeSystemProperty(
            code="evidenceLevel",
            description="Evidence Level", 
            type='string'
            ),
            CodeSystemProperty(
            code="url",
            description="URL",
            type='string'
            ),
            CodeSystemProperty(
            code="alleleType",
            description="Allele Type",
            type='string'
            ),
            CodeSystemProperty(
            code="hgvs",
            description="HGVS",
            type='string'
            )
        ]

        print(f"Processing data from {LOCAL_DATA_FILE}...")
        with open(LOCAL_DATA_FILE, 'r') as file:
            data = json.load(file)

        if data:
            for a in data:
                c = utils.new_CodeSystemConcept(system=pvCS, code=a['pvId'], display=a['alleleName'], definition=a['description'])
                if c is not None:
                    for p in pvCS.property:
                        utils.new_CodeSystemConceptProperty(concept=c, code=p.code, type=p.type, value=a.get(p.code, ''))
 
            with open(LOCAL_CODESYSTEM_FILE, 'w') as file:
                print(f"Saving processed CodeSystem to {LOCAL_CODESYSTEM_FILE}...")
                file.write(pvCS.json(indent=2))
    
        else:
            print("No records found in the data file.")