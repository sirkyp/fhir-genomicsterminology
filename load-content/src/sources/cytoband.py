import os
import csv

from fhir.resources.codesystem import CodeSystem, CodeSystemConcept, CodeSystemProperty

import utils.utils as utils

SOURCE_DATA_FILE_URL = "https://hgdownload.soe.ucsc.edu/goldenPath/hg38/database/cytoBand.txt.gz"
SOURCE_CODESYSTEM_URL = ""  # Updated URL
LOCAL_DATA_DIR = "./data/cytoband"
LOCAL_DATA_FILE = f"{LOCAL_DATA_DIR}/source_data.txt"
LOCAL_CODESYSTEM_FILE = f"{LOCAL_DATA_DIR}/codesystem.json"

class Cytoband:
  def __init__(self):
    """
    Initialize the Cytoband class.
    """
    # Ensure the data directory exists
    os.makedirs(LOCAL_DATA_DIR, exist_ok=True)

  def load_data(self):
    """
    Load data from the Cytoband source and save it to a file.
    """
    print("Loading Cytoband data...")
    
    if utils.is_file_fresh(LOCAL_DATA_FILE, 24):
        return

    utils.download_file(SOURCE_DATA_FILE_URL, LOCAL_DATA_FILE)


  def process_data(self):
    """
    Process the Cytoband data and create FHIR CodeSystem concepts.
    """
    print("Processing Cytoband data")

    if not os.path.exists(LOCAL_DATA_FILE):
      print(f"{LOCAL_DATA_FILE} data file does not exist.")
      return

    print("Creating FHIR CodeSystem for Cytoband...")
    cytobandCS = CodeSystem(status="active", content="complete")
    cytobandCS.name = "Cytoband"
    cytobandCS.title = "Chromosome Bands Localized by FISH Mapping Clones"
    cytobandCS.url = "http://hl7.org/fhir/uv/molecular-definition-data-types/CodeSystem/cytoband"
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

HL7 CG Description
This CodeSystem contains additional cytobands from the UCSC content. For each chromosome, and additional concept is added for the p and q arms, e.g. 1p, 1q, 2p, 2q, etc.
We also remove bands with 'alt', 'fix', 'Un_', '_random' in the name, as these are not standard cytobands.
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
    print(f"Processing {LOCAL_DATA_FILE} data file.")
    with open(LOCAL_DATA_FILE, 'r') as file:
        reader = csv.DictReader(file, delimiter='\t', fieldnames=['chrom', 'start', 'end', 'id', 'giestain'])
        for a in reader:
            code = f"{a['chrom'][3:]}{a['id']}"
            if 'alt' in code or 'fix' in code or 'Un_' in code or '_random' in code:
                # Skip non-standard cytobands
                continue
            concept = utils.new_CodeSystemConcept(system=cytobandCS, code=code, display=code)
            if concept is not None:
              for p in cytobandCS.property:
                # Add properties to the concept
                utils.new_CodeSystemConceptProperty(concept=concept, code=p.code, type=p.type, value=a[p.code])
  
        # Add additional concepts for chromosome arms (the data doesn't have these)
        for c in range(1, 24):
          utils.new_CodeSystemConcept(system=cytobandCS, code=f"{c}p", display=f"{c}p"), 
          utils.new_CodeSystemConcept(system=cytobandCS, code=f"{c}q", display=f"{c}q")

        utils.new_CodeSystemConcept(system=cytobandCS, code="Xp", display="Xp"),
        utils.new_CodeSystemConcept(system=cytobandCS, code="Xq", display="Xq"),
        utils.new_CodeSystemConcept(system=cytobandCS, code="Yp", display="Yp"),
        utils.new_CodeSystemConcept(system=cytobandCS, code="Yq", display="Yq")

    with open(LOCAL_CODESYSTEM_FILE, 'w') as file:
      # Save the processed CodeSystem to a file
      print(f"Saving processed CodeSystem to {LOCAL_CODESYSTEM_FILE}...")
      file.write(cytobandCS.json(indent=2))
