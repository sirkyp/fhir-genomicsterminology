import re

def extract_subclasses(input_file):
    """
    Extract labels of classes that are subClassOf C13432.
    
    Args:
        input_file: Path to source data file
        output_file: Path to save extracted labels
    """    
    labels = []
      # Define namespaces
    namespaces = {
        'owl': 'http://www.w3.org/2002/07/owl#',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#'
    }

    print(f"Processing file: {input_file}")
    # Read and parse JSON
    import xml.etree.ElementTree as ET
    tree = ET.parse(input_file)
    data = tree.getroot()
        
    
    # Find all class elements
    print("Finding classes...")
    classes = data.findall('.//owl:Class', namespaces)
    for class_elem in classes:
      # Look for subClassOf elements
      for subclass in class_elem.findall('./rdfs:subClassOf', namespaces):
        # Check if the resource reference is C13432
        resource = subclass.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
        if resource and resource.endswith('#C13432'):
            # Get the label for this class
            label_elem = class_elem.find('.//{http://www.w3.org/2000/01/rdf-schema#}label')
            if label_elem is not None and label_elem.text:
              labels.append(label_elem.text)
            break
    
    # Sort labels alphabetically
    print(f"Found {len(labels)} labels.")
    labels.sort()

    return labels

def process_cytobands(input_file):
    """
    Process cytoband data to create concatenated band identifiers.
    
    Args:
        input_file: Path to source data file
        output_file: Path to save processed data
    """
    processed_lines = []
    
    with open(input_file, 'r') as f:
        for line in f:
            # Split line on tabs
            columns = line.strip().split('\t')
            
            # Extract chromosome (col 1) and band (col 4)
            chromosome = columns[0].replace('chr', '')
            band = columns[3]
            
            # Concatenate chromosome and band
            code = f"{chromosome}{band}"
            if not ('alt' in code or 'fix' in code or 'Un_' in code or '_random' in code):
              processed_lines.append(code)
    
    processed_lines.sort()  # Sort the results alphabetically
    print(f"Processed {len(processed_lines)} cytoband entries.")
    
    return processed_lines
  
if __name__ == "__main__":
    input_file = "data/cytoband/source_data.txt"
    cytobands = process_cytobands(input_file)
    
    #may have to manually download Thesaurus.owl.txt from https://evs.nci.nih.gov/ftp1/Thesaurus/Thesaurus.owl.txt
    input_file = "data/cytoband/Thesaurus.owl.txt"
    classes = extract_subclasses(input_file)

    combined = {}
    for c in classes:
        item = {'name': c, 'in_nci': True, 'in_ucsc': c in cytobands}
        combined[c] = item
        
    for c in cytobands:
        if c not in combined:
            item = {'name': c, 'in_nci': False, 'in_ucsc': True}
            combined[c] = item
    
    # sort combined results by name
    combined = dict(sorted(combined.items(), key=lambda item: item[0]))

    # Write combined results to a file
    combined_output_file = "data/cytoband/nci_ucsc_comparison.csv"
    with open(combined_output_file, 'w') as f:
        f.write("Chr,Band,NCI,UCSC\n")
        for item in combined.values():
            # get the chromosome and band from the name. It does not have 'chr' prefix, but the chr is always a number before a 'p' or 'q', or X or Y
            chr = -1
            name = item['name']
            match = re.match(r'([0-9XY]+)', name)
            chr = match.group(1) if match else -1
            if chr != -1:
                f.write(f"{chr},{name},{'NCI' if item['in_nci'] else ''},{'UCSC' if item['in_ucsc'] else ''}\n")
  
    print(f"Combined results saved to {combined_output_file}")