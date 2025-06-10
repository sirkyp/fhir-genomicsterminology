import os
import csv

import utils.utils as utils
from fhir.codesystem import FHIRCodeSystem

GENE_SOURCE_DATA_FILE_URL = "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt"
GENE_SOURCE_CODESYSTEM_URL = "https://terminology.hl7.org/CodeSystem-v3-hgnc.json"
GENE_LOCAL_DATA_DIR = "./data/hgnc"
GENE_LOCAL_DATA_FILE = f"{GENE_LOCAL_DATA_DIR}/source_data.tsv"
GENE_LOCAL_CODESYSTEM_FILE = f"{GENE_LOCAL_DATA_DIR}/codesystem.json"

GENEGROUP_SOURCE_DATA_FILE_URL = "https://storage.googleapis.com/public-download-files/hgnc/csv/csv/genefamily_db_tables/family.csv"
GENEGROUP_SOURCE_CODESYSTEM_URL = "https://terminology.hl7.org/CodeSystem-HGNCGeneGroup.json"
GENEGROUP_LOCAL_DATA_DIR = "./data/hgnc"
GENEGROUP_LOCAL_DATA_FILE = f"{GENEGROUP_LOCAL_DATA_DIR}/group_source_data.tsv"
GENEGROUP_LOCAL_CODESYSTEM_FILE = f"{GENEGROUP_LOCAL_DATA_DIR}/group_codesystem.json"

class HGNC:
    def __init__(self):
        """
        Initialize the HGNC class.
        """
        # Ensure the data directory exists
        os.makedirs(GENE_LOCAL_DATA_DIR, exist_ok=True)

    def load_genes(self):
        print("Loading HGNC gene data...")
        if utils.is_file_fresh(GENE_LOCAL_DATA_FILE, 24):
            return

        utils.download_file(GENE_SOURCE_DATA_FILE_URL, GENE_LOCAL_DATA_FILE)

    def load_gene_groups(self):
        print("Loading HGNC gene group data...")
        if utils.is_file_fresh(GENEGROUP_LOCAL_DATA_FILE, 24):
            return

        utils.download_file(GENEGROUP_SOURCE_DATA_FILE_URL, GENEGROUP_LOCAL_DATA_FILE)

    def load_data(self):
        """
        Load data from the HGNC API and save it to a file.
        """
        #download the HGNC data from the provided URL
        print("Loading HGNC data...")

        self.load_genes()
        self.load_gene_groups()

    def process_genes(self):
        """
        Process the HGNC gene data and create FHIR CodeSystem concepts.
        """
        print("Processing HGNC gene data...")

        if not os.path.exists(GENE_LOCAL_DATA_FILE):
            print(f"{GENE_LOCAL_DATA_FILE} data file does not exist.")
            return

        # This method should read the HGNC gene data file and process it
        # to create FHIR CodeSystem concepts.
        print(f"Download CodeSystem from {GENE_SOURCE_CODESYSTEM_URL}...")

        hgncCS = FHIRCodeSystem()
        hgncCS.fetch_cs(url=GENE_SOURCE_CODESYSTEM_URL)
        hgncCS.add_property(code="locus_group", description="The group of genes that share a common locus", type=FHIRCodeSystem.PropertyType.STRING)
        hgncCS.add_property(code="locus_type", description="The type of locus (e.g., protein coding, non-coding)", type=FHIRCodeSystem.PropertyType.STRING)
        hgncCS.add_property(code="location", description="The chromosomal location of the gene", type=FHIRCodeSystem.PropertyType.STRING)
        hgncCS.add_property(code="ensembl_gene_id", description="The Ensembl identifier for the gene", type=FHIRCodeSystem.PropertyType.STRING)
        hgncCS.add_property(code="refseq_accession", description="The RefSeq accession number for the gene", type=FHIRCodeSystem.PropertyType.STRING)
 
        print(f"Processing data from {GENE_LOCAL_DATA_FILE}...")
        with open(GENE_LOCAL_DATA_FILE, 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for a in reader:
                c = hgncCS.add_concept(code=a['hgnc_id'], display=a['symbol'], definition=a['name'])
                for p in hgncCS.property:
                    c.add_property(code=p.code, value=a[p.code], type=p.type)

            with open(GENE_LOCAL_CODESYSTEM_FILE, 'w') as file:
                # Save the processed CodeSystem to a file
                print(f"Saving processed CodeSystem to {GENE_LOCAL_CODESYSTEM_FILE}...")
                file.write(hgncCS.to_json())

    def process_gene_groups(self):
        """
        Process the HGNC gene group data and create FHIR CodeSystem concepts.
        """
        print("Processing HGNC gene group data...")

        if not os.path.exists(GENEGROUP_LOCAL_DATA_FILE):
            print(f"{GENEGROUP_LOCAL_DATA_FILE} data file does not exist.")
            return

        # This method should read the HGNC gene group data file and process it
        # to create FHIR CodeSystem concepts.
        print(f"Download CodeSystem from {GENEGROUP_SOURCE_CODESYSTEM_URL}...")
        hgncCS = FHIRCodeSystem()
        hgncCS.fetch_cs(url=GENEGROUP_SOURCE_CODESYSTEM_URL)
 
        print(f"Processing data from {GENEGROUP_LOCAL_DATA_FILE}...")
        with open(GENEGROUP_LOCAL_DATA_FILE, 'r') as file:
            reader = csv.DictReader(file, delimiter=',', quotechar='"')

            for a in reader:
                c = hgncCS.add_concept(code=a['id'], display=a['abbreviation'], definition=a['name'])

            with open(GENEGROUP_LOCAL_CODESYSTEM_FILE, 'w') as file:
                # Save the processed CodeSystem to a file
                print(f"Saving processed CodeSystem to {GENEGROUP_LOCAL_CODESYSTEM_FILE}...")
                file.write(hgncCS.to_json())
    
    def process_data(self):
        """
        Process the HGNC data and create FHIR CodeSystem concepts.
        """
        print("Processing HGNC data...")
        self.process_genes()
        self.process_gene_groups()
