from pathlib import Path
import csv
import utils.utils as utils
from fhir.resources.codesystem import CodeSystem, CodeSystemConcept, CodeSystemProperty

SOURCE_DATA_FILE_URL = "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/variant_summary.txt.gz"
SOURCE_CODESYSTEM_URL = "https://terminology.hl7.org/CodeSystem-ClinVarV.json"
LOCAL_DATA_DIR = Path("./data/clinvar")
LOCAL_DATA_FILE = LOCAL_DATA_DIR / "variant_summary.txt"
LOCAL_CODESYSTEM_FILE = LOCAL_DATA_DIR / "codesystem.json"

class ClinVar:
  def __init__(self):
    """
    Initialize the ClinVar class.
    """
    # Ensure the data directory exists
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)

  def load_data(self):
    """
    Check if the ClinVar data file exists locally.
    """
    print("Checking for ClinVar data file...")

    if utils.is_file_fresh(LOCAL_DATA_FILE, 24*7):  # Check if the file is fresh (not older than 7 days)
        return

    utils.download_file(SOURCE_DATA_FILE_URL, LOCAL_DATA_FILE)

  def process_data(self):
    """
    Process the ClinVar TSV data and create FHIR CodeSystem concepts.
    Uses chunked reading for large file handling.
    """
    print("Processing ClinVar data file...")

    if not LOCAL_DATA_FILE.exists():
      print(f"ERROR: {LOCAL_DATA_FILE} data file does not exist. Please ensure the file is present.")
      return

    if utils.is_file_fresh(LOCAL_CODESYSTEM_FILE, 24*7):
      print(f"ClinVar CodeSystem file {LOCAL_CODESYSTEM_FILE} is fresh. Skipping processing.")
      return

    print(f"Loading ClinVar CodeSystem from {SOURCE_CODESYSTEM_URL}...")
    clinvarCS = utils.new_CodeSystemFromURL(SOURCE_CODESYSTEM_URL)

    clinvarCS.property = [
      CodeSystemProperty(code="ClinicalSignificance", description="Clinical Significance",type='string'),
      CodeSystemProperty(code="GeneSymbol", description="Gene Symbol", type='string')
    ]

    # Process the large TSV file in chunks
    chunk_size = 50000  # Adjust this based on your memory constraints
    processed_count = 0

    try:
      print(f"Processing data from {LOCAL_DATA_FILE}...")
      with LOCAL_DATA_FILE.open('r') as file:
        # tab-separated file with headers
        csv_reader = csv.DictReader(file, delimiter='\t')
        
        batch = []
        for row in csv_reader:

          # Add concept to batch
          # for now, only use GRCh38 as the reference genome
          if 'GRCh38' in row.get('Assembly', ''):
            code = row.get('VariationID', '')
            display = row.get('Name', '')
            definition = ''
            props = {}
            for p in clinvarCS.property:
              props[p.code] = row.get(p.code, '')

            batch.append({
              'code': code,
              'display': display,
              'definition': definition,
              'property': props
            })

          if len(batch) >= chunk_size:
            # Process batch
            print('.', end='', flush=True)
            for item in batch:
              concept = utils.new_CodeSystemConcept(system=clinvarCS, code=item['code'], display=item['display'], definition=item['definition'])
              if concept is not None:
                for p in clinvarCS.property: 
                  utils.new_CodeSystemConceptProperty(concept=concept, code=p.code, type=p.type, value=item['property'].get(p.code, ''))

            processed_count += len(batch)
            batch = []

        # Process remaining records
        if batch:
          print('.', end='', flush=True)
          for item in batch:
              concept = utils.new_CodeSystemConcept(system=clinvarCS, code=item['code'], display=item['display'], definition=item['definition'])
              if concept is not None:
                for p in clinvarCS.property: 
                  utils.new_CodeSystemConceptProperty(concept=concept, code=p.code, type=p.type, value=item['property'].get(p.code, ''))

          processed_count += len(batch)

      print(f"Total records processed: {processed_count}")
  
      # Save the processed CodeSystem to a file
      print(f"Saving processed CodeSystem to {LOCAL_CODESYSTEM_FILE}...")
      LOCAL_CODESYSTEM_FILE.write_text(clinvarCS.model_dump_json(indent=2))

    except Exception as e:
      print(f"Error processing file: {str(e)}")
