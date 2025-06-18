from pathlib import Path
import csv
import json
import utils.utils as utils

from fhir.resources.codesystem import CodeSystem, CodeSystemProperty
from fhir.resources.valueset import ValueSet, ValueSetCompose, ValueSetComposeInclude, ValueSetComposeIncludeConcept

SOURCE_CODESYSTEM_URL = ""  # Updated URL
LOCAL_DATA_DIR = Path("./data/cytoband")

UCSC_SOURCE_DATA_FILE_URL = "https://hgdownload.soe.ucsc.edu/goldenPath/hg38/database/cytoBand.txt.gz"
UCSC_LOCAL_DATA_FILE = LOCAL_DATA_DIR / "ucsc_source_data.txt"
UCSC_LOCAL_CODESYSTEM_FILE = LOCAL_DATA_DIR / "ucsc_codesystem.json"

NCIT_SOURCE_DATA_API_URL = "https://api-evsrest.nci.nih.gov/api/v1/concept/ncit/C13432/children"
NCIT_LOCAL_DATA_FILE = LOCAL_DATA_DIR / "ncit_source_data.json"
NCIT_LOCAL_CODESYSTEM_FILE = LOCAL_DATA_DIR / "ncit_codesystem.json"

LOCAL_VALUESET_FILE = LOCAL_DATA_DIR / "valueset.json"

class Cytoband:
  def __init__(self):
    """
    Initialize the Cytoband class.
    """
    # Ensure the data directory exists
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)

  def load_data(self):
    """
    Load data from the Cytoband source and save it to a file.
    """
    print("Loading Cytoband data...")
    
    self.load_data_ucsc()
    self.load_data_ncit()

  def load_data_ucsc(self):
    """
    Load data from the Cytoband source and save it to a file.
    """
    print("Loading UCSC Cytoband data...")
    
    if utils.is_file_fresh(UCSC_LOCAL_DATA_FILE, 24):
        return

    utils.download_file(UCSC_SOURCE_DATA_FILE_URL, UCSC_LOCAL_DATA_FILE)

  def load_data_ncit(self):
    """
    Load data from the NCI Thesaurus source and save it to a file.
    """
    print("Loading NCI Thesaurus Cytoband data...")

    if utils.is_file_fresh(NCIT_LOCAL_DATA_FILE, 24):
        return

    utils.download_file(NCIT_SOURCE_DATA_API_URL, NCIT_LOCAL_DATA_FILE)

  def process_data(self):
    """
    Process the Cytoband data and create FHIR CodeSystem concepts.
    """
    print("Processing Cytoband data...")

    self.process_data_ucsc()
    self.process_data_ncit()
    
    self.create_valueset()
  
  def process_data_ncit(self):
    """
    Process the NCI Thesaurus data and create FHIR CodeSystem concepts.
    """
    print("Processing NCI Thesaurus Cytoband data")

    if not NCIT_LOCAL_DATA_FILE.exists():
      print(f"{NCIT_LOCAL_DATA_FILE} data file does not exist.")
      return

    print("Creating FHIR CodeSystem for NCI Thesaurus...")
    ncitCS = CodeSystem(status="active", content="fragment")
    ncitCS.name = "NCI Thesaurus Cytobands"
    ncitCS.title = "NCI Thesaurus Cytobands"
    ncitCS.url = "http://hl7.org/fhir/uv/molecular-definition-data-types/CodeSystem/nci-cytoband"
    ncitCS.version = "1.0.0"
    ncitCS.experimental = True
    ncitCS.publisher = "HL7 Clinical Genomics WG"
    ncitCS.description = ""
    ncitCS.contact=[{"name": "NCI Thesaurus", "telecom": [{"system": "url", "value": "https://evs.nci.nih.gov/"}]}]
    ncitCS.relatedArtifact=[{"type": "documentation", "label": "NCI Thesaurus Cytoband API", "document": {"url": NCIT_SOURCE_DATA_API_URL} }]
    
    # read and parse a JSON file, that looks like this:
    data = {}
    with NCIT_LOCAL_DATA_FILE.open('r') as file:
      data = json.load(file)

    if not data:
      print(f"No data found in {NCIT_LOCAL_DATA_FILE}.")
      return

    print(f"Processing {len(data)} concepts from NCI Thesaurus data file.")
    for concept in data:
      code = concept.get('code')
      display = concept.get('name')

      if not code or not display:
        print(f"Skipping concept with missing code or display: {concept}")
        continue

      # Create the CodeSystemConcept
      utils.new_CodeSystemConcept(system=ncitCS, code=code, display=display)

    # write the CodeSystem to a file
    print(f"Saving processed CodeSystem to {NCIT_LOCAL_CODESYSTEM_FILE}...")
    NCIT_LOCAL_CODESYSTEM_FILE.write_text(ncitCS.model_dump_json(indent=2))

  def process_data_ucsc(self):
    """
    Process the Cytoband data and create FHIR CodeSystem concepts.
    """
    print("Processing UCSC Cytoband data")

    if not UCSC_LOCAL_DATA_FILE.exists():
      print(f"{UCSC_LOCAL_DATA_FILE} data file does not exist.")
      return

    print("Creating FHIR CodeSystem for Cytoband...")
    cytobandCS = CodeSystem(status="active", content="complete")
    cytobandCS.name = "Cytoband"
    cytobandCS.title = "Chromosome Bands Localized by FISH Mapping Clones"
    cytobandCS.url = "http://hl7.org/fhir/uv/molecular-definition-data-types/CodeSystem/ucsc-cytoband"
    cytobandCS.version = "1.0.0"
    cytobandCS.experimental = True
    cytobandCS.publisher = "HL7 Clinical Genomics WG"
    cytobandCS.description = ""
    cytobandCS.contact=[{"name": "UCSC Genome Browser", "telecom": [{"system": "url", "value": "https://genome.ucsc.edu/"}]}]
    cytobandCS.relatedArtifact=[{"type": "documentation", "label": "UCSC Cytoband Track", "document": {"url": "https://genome.ucsc.edu/cgi-bin/hgTables?hgsid=2635207210_psoFu973UsC7wWlBbsqfQvoIWWYo&clade=mammal&org=Human&db=hg38&hgta_group=map&hgta_track=cytoBand&hgta_table=0&hgta_regionType=genome&position=chr7%3A155%2C799%2C529-155%2C812%2C871&hgta_outputType=primaryTable&hgta_outFileName="}}]
    cytobandCS.description = """
Description
The chromosome band track represents the approximate location of bands seen on Giemsa-stained chromosomes. Chromosomes are displayed in the browser with the short arm first. Cytologically identified bands on the chromosome are numbered outward from the centromere on the short (p) and long (q) arms. At low resolution, bands are classified using the nomenclature [chromosome][arm][band], where band is a single digit. Examples of bands on chromosome 3 include 3p2, 3p1, cen, 3q1, and 3q2. At a finer resolution, some of the bands are subdivided into sub-bands, adding a second digit to the band number, e.g. 3p26. This resolution produces about 500 bands. A final subdivision into a total of 862 sub-bands is made by adding a period and another digit to the band, resulting in 3p26.3, 3p26.2, etc.

Methods
Chromosome band information was downloaded from NCBI using the ideogram.gz file for the respective assembly. These data were then transformed into our visualization format. See our assembly creation documentation for the organism of interest to see the specific steps taken to transform these data. Band lengths are typically estimated based on FISH or other molecular markers interpreted via microscopy.

For some of our older assemblies, greater than 10 years old, the tracks were created as detailed below and in Furey and Haussler, 2003.

Barbara Trask, Vivian Cheung, Norma Nowak and others in the BAC Resource Consortium used fluorescent in-situ hybridization (FISH) to determine a cytogenetic location for large genomic clones on the chromosomes. The results from these experiments are the primary source of information used in estimating the chromosome band locations. For more information about the process, see the paper, Cheung, et al., 2001. and the accompanying web site, Human BAC Resource.

BAC clone placements in the human sequence are determined at UCSC using a combination of full BAC clone sequence, BAC end sequence, and STS marker information.
    """

    cytobandCS.property = [
      CodeSystemProperty(
        code="start",
        type='integer',
        description="Chromosome Start (0-based)"
      ),
      CodeSystemProperty(
        code="end",
        type='integer',
        description="Chromosome End (0-based)"
      ),
      CodeSystemProperty(
        code="giestain", 
        type='string',
        description="gieStain"
      )
    ]

    data = []
    print(f"Processing {UCSC_LOCAL_DATA_FILE} data file.")
    with UCSC_LOCAL_DATA_FILE.open('r') as file:
        reader = csv.DictReader(file, delimiter='\t', fieldnames=['chrom', 'start', 'end', 'id', 'giestain'])
        for a in reader:
            code = f"{a['chrom'][3:]}{a['id']}"
            concept = utils.new_CodeSystemConcept(system=cytobandCS, code=code, display=code)
            if concept is not None:
              for p in cytobandCS.property:
                # Add properties to the concept
                utils.new_CodeSystemConceptProperty(concept=concept, code=p.code, type=p.type, value=a[p.code])
  
    print(f"Saving processed CodeSystem to {UCSC_LOCAL_CODESYSTEM_FILE}...")
    UCSC_LOCAL_CODESYSTEM_FILE.write_text(cytobandCS.model_dump_json(indent=2))


  def create_valueset(self):
    """
    Create a FHIR ValueSet for the cytobands, joining together the UCSC and NCI code systems.
    """
    print("Creating FHIR ValueSet for Cytoband...")

    # Load the UCSC CodeSystem
    if not UCSC_LOCAL_CODESYSTEM_FILE.exists():
      print(f"{UCSC_LOCAL_CODESYSTEM_FILE} does not exist. Please run process_data() first.")
      return
    with UCSC_LOCAL_CODESYSTEM_FILE.open('r') as file:
      ucscCS = CodeSystem.model_validate_json(file.read())

    # Load the NCI CodeSystem
    if not NCIT_LOCAL_CODESYSTEM_FILE.exists():
      print(f"{NCIT_LOCAL_CODESYSTEM_FILE} does not exist. Please run process_data() first.")
      return
    with NCIT_LOCAL_CODESYSTEM_FILE.open('r') as file:
      ncitCS = CodeSystem.model_validate_json(file.read())
  
    # Create the ValueSet
    cytobandVS = ValueSet.model_construct()
    cytobandVS.status = "active"
    cytobandVS.name = "Cytoband ValueSet"
    cytobandVS.title = "Cytoband ValueSet"
    cytobandVS.url = "http://hl7.org/fhir/uv/molecular-definition-data-types/ValueSet/cytoband"
    cytobandVS.version = "1.0.0"
    cytobandVS.experimental = True
    cytobandVS.publisher = "HL7 Clinical Genomics WG"
    cytobandVS.description = """
HL7 CG Description
This ValueSet contains cytobands from NCI Metatherasarus and UCSC content. For each chromosome, an additional concept is added for the p and q arms, e.g. 1p, 1q, 2p, 2q, etc.
For the content that overlaps between UCSC and NCI, we use the NCI code.
From UCSC, we remove bands with 'alt', 'fix', 'Un_', '_random' in the name, as these are not standard cytobands.
From NCI, we remove bands with ranges that are not standard cytobands, e.g. 'Cytoband: 1p36.33-1p36.32'.
    """

    bands = set()

    # Include NCIT codes
    ncit_include = ValueSetComposeInclude()
    ncit_include.system = ncitCS.url
    ncit_include.version = ncitCS.version
    ncit_include.concept = []
    # Add all concepts from the NCI CodeSystem
    for concept in ncitCS.concept:
        if concept.code:  # Ensure the code is not None
          # filter out non-standard cytobands
          code = concept.code
          display = concept.display
          if '-' in display or 'Chromosome Band' in display:
            continue  # Skip ranges like 'Cytoband: 1p36.33-1p36.32'

          ncit_include.concept.append(ValueSetComposeIncludeConcept(code=code, display=display))
          # in NCI, the display is the band name, so we can use it as a key
          bands.add(display)

    # Include UCSC codes
    ucsc_include = ValueSetComposeInclude()
    ucsc_include.system = ucscCS.url
    ucsc_include.version = ucscCS.version
    ucsc_include.concept = []
    # Add all concepts from the UCSC CodeSystem
    for concept in ucscCS.concept:
      if concept.code:  # Ensure the code is not None
        code = concept.code
        # Skip non-standard cytobands and bands that are already in the NCI list
        if ('alt' in code or 'fix' in code or 'Un_' in code or '_random' in code or 
            code in bands):  # Check if the code is in bands dictionary (in UCSC, code is the band name)
            continue

        ucsc_include.concept.append(ValueSetComposeIncludeConcept(code=code, display=concept.display))
        bands.add(code)

    # add a new include and include custom codes for p and q arms on all chromosomes  
    custom_include = ValueSetComposeInclude()
    custom_include.system = "chromome-arm-codes"
    custom_include.concept = []
    # Add codes for chromosomes 1-22, X, and Y
    for i in list(range(1, 23)) + ['X', 'Y']:
        p_code = f"{i}p"
        q_code = f"{i}q"
        if p_code not in bands:
            custom_include.concept.append(ValueSetComposeIncludeConcept(code=p_code, display=p_code))
            bands.add(p_code)
        if q_code not in bands:
            custom_include.concept.append(ValueSetComposeIncludeConcept(code=q_code, display=q_code))
            bands.add(q_code)

    cytobandVS.compose = ValueSetCompose(include = [ncit_include,ucsc_include,custom_include])

    # Save the ValueSet to a file
    print(f"Saving ValueSet to {LOCAL_VALUESET_FILE}...")
    LOCAL_VALUESET_FILE.write_text(cytobandVS.model_dump_json(indent=2))
    
    print("ValueSet created successfully.")    
  