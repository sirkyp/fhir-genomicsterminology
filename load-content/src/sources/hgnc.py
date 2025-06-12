from pathlib import Path
import csv

import utils.utils as utils
from fhir.resources.codesystem import CodeSystem, CodeSystemConcept, CodeSystemProperty

LOCAL_DATA_DIR = Path("./data/hgnc")

GENE_SOURCE_DATA_FILE_URL = "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt"
GENE_SOURCE_CODESYSTEM_URL = "https://terminology.hl7.org/CodeSystem-v3-hgnc.json"
GENE_LOCAL_DATA_FILE = LOCAL_DATA_DIR / "source_data.tsv"
GENE_LOCAL_CODESYSTEM_FILE = LOCAL_DATA_DIR / "codesystem.json"

GENEGROUP_SOURCE_DATA_FILE_URL = "https://storage.googleapis.com/public-download-files/hgnc/csv/csv/genefamily_db_tables/family.csv"
GENEGROUP_SOURCE_CODESYSTEM_URL = "https://terminology.hl7.org/CodeSystem-HGNCGeneGroup.json"
GENEGROUP_LOCAL_DATA_FILE = LOCAL_DATA_DIR / "group_source_data.tsv"
GENEGROUP_LOCAL_CODESYSTEM_FILE = LOCAL_DATA_DIR / "group_codesystem.json"

class HGNC:
    def __init__(self):
        """
        Initialize the HGNC class.
        """
        # Ensure the data directory exists
        LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)

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

        if not GENE_LOCAL_DATA_FILE.exists():
            print(f"{GENE_LOCAL_DATA_FILE} data file does not exist.")
            return

        # This method should read the HGNC gene data file and process it
        # to create FHIR CodeSystem concepts.
        print(f"Download CodeSystem from {GENE_SOURCE_CODESYSTEM_URL}...")

        hgncCS = utils.new_CodeSystemFromURL(url=GENE_SOURCE_CODESYSTEM_URL)

        hgncCS.property = [
            CodeSystemProperty(
                code="locus_group",
                description="The group of genes that share a common locus",
                type='string'
            ),
            CodeSystemProperty(
                code="locus_type", 
                description="The type of locus (e.g., protein coding, non-coding)",
                type='string'
            ),
            CodeSystemProperty(
                code="location",
                description="The chromosomal location of the gene",
                type='string'
            ),
            CodeSystemProperty(
                code="ensembl_gene_id",
                description="The Ensembl identifier for the gene", 
                type='string'
            ),
            CodeSystemProperty(
                code="refseq_accession",
                description="The RefSeq accession number for the gene",
                type='string'
            ),
            CodeSystemProperty(
                code="gene_group",
                description="The gene group/family name",
                type='string'
            ),
            CodeSystemProperty(
                code="gene_group_id", 
                description="The gene group/family ID",
                type='string'
            ),
            CodeSystemProperty(
                code="alias_symbol",
                description="Alternative symbols used to refer to the gene",
                type='string'
            ),
            CodeSystemProperty(
                code="alias_name",
                description="Alternative names used to refer to the gene",
                type='string'
            )
        ]
 
        print(f"Processing data from {GENE_LOCAL_DATA_FILE}...")
        with GENE_LOCAL_DATA_FILE.open('r') as file:
            reader = csv.DictReader(file, delimiter='\t')

            for a in reader:
                c = utils.new_CodeSystemConcept(system=hgncCS, code=a['hgnc_id'], display=a['symbol'], definition=a['name'])
                if c is not None:
                    for p in hgncCS.property:
                        # Add properties to the concept
                        utils.new_CodeSystemConceptProperty(concept=c, code=p.code, type=p.type, value=a[p.code])

        print(f"Saving processed CodeSystem to {GENE_LOCAL_CODESYSTEM_FILE}...")
        GENE_LOCAL_CODESYSTEM_FILE.write_text(hgncCS.model_dump_json(indent=2))

    def process_gene_groups(self):
        """
        Process the HGNC gene group data and create FHIR CodeSystem concepts.
        """
        print("Processing HGNC gene group data...")

        if not GENEGROUP_LOCAL_DATA_FILE.exists():
            print(f"{GENEGROUP_LOCAL_DATA_FILE} data file does not exist.")
            return

        # This method should read the HGNC gene group data file and process it
        # to create FHIR CodeSystem concepts.
        print(f"Download CodeSystem from {GENEGROUP_SOURCE_CODESYSTEM_URL}...")
        hgncCS = utils.new_CodeSystemFromURL(url=GENEGROUP_SOURCE_CODESYSTEM_URL)

        print(f"Processing data from {GENEGROUP_LOCAL_DATA_FILE}...")
        with GENEGROUP_LOCAL_DATA_FILE.open('r') as file:
            reader = csv.DictReader(file, delimiter=',', quotechar='"')

            for a in reader:
                utils.new_CodeSystemConcept(system=hgncCS, code=a['id'], display=a['abbreviation'], definition=a['name'])

        print(f"Saving processed CodeSystem to {GENEGROUP_LOCAL_CODESYSTEM_FILE}...")
        GENEGROUP_LOCAL_CODESYSTEM_FILE.write_text(hgncCS.model_dump_json(indent=2))
    
    def process_data(self):
        """
        Process the HGNC data and create FHIR CodeSystem concepts.
        """
        print("Processing HGNC data...")
        self.process_genes()
        self.process_gene_groups()
