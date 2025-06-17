# fhir-genomicsterminology

## Overview
This project is for creating some FHIR terminology resources for genomic terminologies. Here is a description of the resources and where the original content comes from:
* HGCN (Genes and GeneGroups)
  - [https://www.genenames.org/download/]
* ClinVar
  - [https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/README] (variant_summary.txt)
* PharmVar
  - [https://www.pharmvar.org/documentation] (Alleles service)
* RefSeq (for now, MANE transcripts only)
  - [https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/release_1.4/README.txt] (MANE.GRCh38.v##.summary.txt.gz)
* SequenceOntology
  - [https://github.com/The-Sequence-Ontology/SO-Ontologies] (Ontology_Files)
* cytobands (union of NCI-T and UCSC Browser data)
  - UCSC - [https://hgdownload.soe.ucsc.edu/goldenPath/hg38/database/] (cytoBand.txt.gz)
  - NCI-T - [https://api-evsrest.nci.nih.gov/swagger-ui/index.html#/Concept%20endpoints/getChildren] (for parent code C13432)
* HPO
  - [https://github.com/obophenotype/human-phenotype-ontology/releases] (hp_full.json)

## Installation
To install the necessary dependencies, run the following command:

```
pip install -r requirements.txt
```

## Usage
To run the application, execute the main script:

```
python src/main.py
```
