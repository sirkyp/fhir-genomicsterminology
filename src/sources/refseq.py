from pathlib import Path
import csv

import utils.utils as utils
from fhir.resources.codesystem import CodeSystem, CodeSystemConcept, CodeSystemProperty

# This source data contains the RefSeq accession numbers from the MANE (Matching Annotated Nucleotide and Protein Sequences) project, which is a subset of the full RefSeq database. This is the scope of the CodeSystem we are creating here (for now)
# The full RefSeq database can be found at the NCBI RefSeq website: https://www.ncbi.nlm.nih.gov/refseq/
SOURCE_DATA_FILE_URL = "https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/release_1.4/MANE.GRCh38.v1.4.summary.txt.gz"
SOURCE_CODESYSTEM_URL = "https://terminology.hl7.org/CodeSystem-v3-refSeq.json"
LOCAL_DATA_DIR = Path("./data/refseq")
LOCAL_DATA_FILE = LOCAL_DATA_DIR / "source_data.txt"
LOCAL_CODESYSTEM_FILE = LOCAL_DATA_DIR / "codesystem.json"

class RefSeq:
  def __init__(self):
    """
    Initialize the RefSeq class.
    """
    # Ensure the data directory exists
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)

  def load_data(self):
    """
    Load data from the RefSeq source and save it to a file.
    """
    print("Loading RefSeq data...")
    
    if utils.is_file_fresh(LOCAL_DATA_FILE, 24):
        return

    utils.download_file(SOURCE_DATA_FILE_URL, LOCAL_DATA_FILE)

  def process_data(self):
    """
    Process the RefSeq data and create FHIR CodeSystem concepts.
    """
    print("Processing RefSeq data...")

    if not LOCAL_DATA_FILE.exists():
      print(f"{LOCAL_DATA_FILE} Data file does not exist.")
      return
  
    print(f"Creating FHIR CodeSystem for RefSeq from {SOURCE_CODESYSTEM_URL}...")
    refseqCS = CodeSystem(status="active", content="complete")
    refseqCS = utils.new_CodeSystemFromURL(url=SOURCE_CODESYSTEM_URL)
  
    refseqCS.status = 'draft'
    refseqCS.content = 'fragment'
    refseqCS.purpose = "RefSeq provides a comprehensive, accurate, and up-to-date collection of sequences, including genomic DNA, transcripts, and proteins for the human genome. NOTE: This CodeSystem only includes the RefSeq accession numbers from MANE (Matching Annotated Nucleotide and Protein Sequences), which is a subset of the full RefSeq database. For the full RefSeq database, please refer to the NCBI RefSeq website."
    refseqCS.relatedArtifact = [{"type": "documentation", "label": "NCBI MANE README", "document": {"url": "https://ftp.ncbi.nlm.nih.gov/refseq/MANE/README.txt"}}]
    
    refseqCS.property = [
      CodeSystemProperty(
        code="HGNC_ID",
        description="HGNC Gene ID assigned by the HUGO Gene Nomenclature Committee",
        type='string'
      ),
      CodeSystemProperty(
        code="symbol", 
        description="Official gene symbol",
        type='string'
      ),
      CodeSystemProperty(
        code="name",
        description="Full name of the gene", 
        type='string'
      ),
      CodeSystemProperty(
        code="GRCh38_chr",
        description="Chromosome location in GRCh38 genome assembly",
        type='string'
      ),
      CodeSystemProperty(
        code="chr_start",
        description="Start position on chromosome",
        type='integer'
      ),
      CodeSystemProperty(
        code="chr_end",
        description="End position on chromosome",
        type='integer'
      )
    ]
  
    print(f"Processing data from {LOCAL_DATA_FILE}...")
    with LOCAL_DATA_FILE.open('r') as file:
      reader = csv.DictReader(file, delimiter="\t")
      for row in reader:
        # skip rows without a valid 'HGNC_ID'
        if row.get("HGNC_ID"):
          for h in ["RefSeq_prot", "RefSeq_nuc"]:
            code = row[h]
            concept = utils.new_CodeSystemConcept(system=refseqCS, code=code, display=code)
            if concept is not None:
              for p in refseqCS.property:
                utils.new_CodeSystemConceptProperty(concept=concept, code=p.code, type=p.type, value=row[p.code])

    print(f"Saving processed CodeSystem to {LOCAL_CODESYSTEM_FILE}...")
    LOCAL_CODESYSTEM_FILE.write_text(refseqCS.model_dump_json(indent=2))
