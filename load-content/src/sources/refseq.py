import os
import csv

import utils.utils as utils
from fhir.codesystem import FHIRCodeSystem

# This source data contains the RefSeq accession numbers from the MANE (Matching Annotated Nucleotide and Protein Sequences) project, which is a subset of the full RefSeq database. This is the scope of the CodeSystem we are creating here (for now)
# The full RefSeq database can be found at the NCBI RefSeq website: https://www.ncbi.nlm.nih.gov/refseq/
SOURCE_DATA_FILE_URL = "https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/release_1.4/MANE.GRCh38.v1.4.summary.txt.gz"
SOURCE_CODESYSTEM_URL = "https://terminology.hl7.org/CodeSystem-v3-refSeq.json"
LOCAL_DATA_DIR = "./data/refseq"
LOCAL_DATA_FILE = f"{LOCAL_DATA_DIR}/source_data.txt"
LOCAL_CODESYSTEM_FILE = f"{LOCAL_DATA_DIR}/codesystem.json"

class RefSeq:
  def __init__(self):
    """
    Initialize the RefSeq class.
    """
    # Ensure the data directory exists
    os.makedirs(LOCAL_DATA_DIR, exist_ok=True)

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

    if not os.path.exists(LOCAL_DATA_FILE):
      print(f"{LOCAL_DATA_DIR} Data file does not exist.")
      return
  
    print(f"Creating FHIR CodeSystem for RefSeq from {SOURCE_CODESYSTEM_URL}...")
    refseqCS = FHIRCodeSystem()
    refseqCS.fetch_cs(url=SOURCE_CODESYSTEM_URL)
  
    refseqCS.status = 'draft'
    refseqCS.content = 'fragment'
    refseqCS.purpose = "RefSeq provides a comprehensive, accurate, and up-to-date collection of sequences, including genomic DNA, transcripts, and proteins for the human genome. NOTE: This CodeSystem only includes the RefSeq accession numbers from MANE (Matching Annotated Nucleotide and Protein Sequences), which is a subset of the full RefSeq database. For the full RefSeq database, please refer to the NCBI RefSeq website."
    refseqCS.relatedArtifact = [{"type": "documentation", "label": "NCBI MANE README", "url": "https://ftp.ncbi.nlm.nih.gov/refseq/MANE/README.txt"}]
    
    refseqCS.add_property(code="HGNC_ID", description="HGNC Gene ID assigned by the HUGO Gene Nomenclature Committee", type=FHIRCodeSystem.PropertyType.STRING)
    refseqCS.add_property(code="symbol", description="Official gene symbol", type=FHIRCodeSystem.PropertyType.STRING)
    refseqCS.add_property(code="name", description="Full name of the gene", type=FHIRCodeSystem.PropertyType.STRING)
    refseqCS.add_property(code="GRCh38_chr", description="Chromosome location in GRCh38 genome assembly", type=FHIRCodeSystem.PropertyType.STRING)
    refseqCS.add_property(code="chr_start", description="Start position on chromosome", type=FHIRCodeSystem.PropertyType.INTEGER)
    refseqCS.add_property(code="chr_end", description="End position on chromosome", type=FHIRCodeSystem.PropertyType.INTEGER)
  
    print(f"Processing data from {LOCAL_DATA_FILE}...")
    with open(LOCAL_DATA_FILE, 'r') as file:
      reader = csv.DictReader(file, delimiter="\t")
      for row in reader:
        # skip rows without a valid 'HGNC_ID'
        if row.get("HGNC_ID"):
          for h in ["RefSeq_prot", "RefSeq_nuc"]:
            code = row[h]
            c = refseqCS.add_concept(code=code, display=code)
            for p in refseqCS.property:
              c.add_property(code=p.code, value=row[p.code], type=p.type)

      with open(LOCAL_CODESYSTEM_FILE, 'w') as outfile:
        print(f"Saving processed CodeSystem to {LOCAL_CODESYSTEM_FILE}...")
        outfile.write(refseqCS.to_json())
