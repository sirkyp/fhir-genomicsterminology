# main.py
from sources.pharmvar import PharmVar
from sources.hgnc import HGNC
from sources.sequenceontology import SequenceOntology
from sources.hpo import HPO
from sources.clinvar import ClinVar
from sources.cytoband import Cytoband
from sources.refseq import RefSeq

def init():
    print("Initializing the project...")

def main():
    sources = []
    sources.append(PharmVar())  # Create an instance of the PharmVar class
    sources.append(SequenceOntology())  # Create an instance of the SequenceOntology class
    sources.append(HPO())  # Create an instance of the HPO class
    sources.append(ClinVar())  # Create an instance of the ClinVar class
    sources.append(Cytoband())  # Create an instance of the Cytoband class
    sources.append(RefSeq())  # Create an instance of the RefSeq class
    sources.append(HGNC())  # Create an instance of the HGNC class

    for s in sources:
        s.load_data()
        s.process_data()

if __name__ == "__main__":
    init()
    main()

