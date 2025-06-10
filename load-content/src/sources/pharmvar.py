import requests
import os
import json
from fhir.codesystem import FHIRCodeSystem
import utils.utils as utils

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
        pvCS = FHIRCodeSystem()
        pvCS.fetch_cs(url=SOURCE_CODESYSTEM_URL)
        pvCS.add_property(code="geneSymbol", description="Gene Symbol", type=FHIRCodeSystem.PropertyType.STRING)
        pvCS.add_property(code="function", description="Function", type=FHIRCodeSystem.PropertyType.STRING)
        pvCS.add_property(code="evidenceLevel", description="Evidence Level", type=FHIRCodeSystem.PropertyType.STRING)
        pvCS.add_property(code="url", description="URL", type=FHIRCodeSystem.PropertyType.STRING)
        pvCS.add_property(code="alleleType", description="Allele Type", type=FHIRCodeSystem.PropertyType.STRING)
        pvCS.add_property(code="hgvs", description="HGVS", type=FHIRCodeSystem.PropertyType.STRING)

        print(f"Processing data from {LOCAL_DATA_FILE}...")
        with open(LOCAL_DATA_FILE, 'r') as file:
            data = json.load(file)

        if data:
            for a in data:
                c = pvCS.add_concept(code=a['pvId'], display=a['alleleName'], definition=a['description'])
                for p in pvCS.property:
                    c.add_property(code=p.code, value=a[p.code], type=p.type)

            with open(LOCAL_CODESYSTEM_FILE, 'w') as file:
                print(f"Saving processed CodeSystem to {LOCAL_CODESYSTEM_FILE}...")
                file.write(pvCS.to_json())
            
        else:
            print("No records found in the data file.")