import time
import requests
import gzip
import shutil
import pathlib
from fhir.resources.codesystem import CodeSystem
from fhir.resources.codesystem import CodeSystemConceptProperty
from fhir.resources.codesystem import CodeSystemConcept

def new_CodeSystemFromURL(url: str) -> CodeSystem:
    """
    Create a new CodeSystem from a URL.
    
    Args:
        url: The URL to fetch the CodeSystem from
    
    Returns:
        CodeSystem: A new CodeSystem instance
    """
    if url is None or len(url) == 0:
        return None

    # given a URL that resolves to a CodeSystem, fetch the data
    try:
        response = requests.get(url)
        if response.status_code == 200:
            code_system = CodeSystem.model_validate(response.json())
        else:
            print(f"Failed to fetch CodeSystem from {url}. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching CodeSystem from {url}: {e}")

    #since we are loading concepts, we can default adding the concept array to the object
    code_system.concept = []

    return code_system


def new_CodeSystemConcept(system: CodeSystem, code: str, display: str = None, definition: str = None) -> CodeSystemConcept:
    """
    Create a new CodeSystemConcept with the given code and optional display.
    
    Args:
        system: The CodeSystem to which the concept will be added
        code: The code for the concept
        display: Optional display name for the concept
    
    Returns:
        CodeSystemConcept: A new CodeSystemConcept instance
    """
    if code is None or len(code) == 0:
        return None

    concept = CodeSystemConcept(code=code)
    if display is not None and len(display) > 0:
        concept.display = display

    if definition is not None and len(definition) > 0:
        concept.definition = definition

    if not system.concept:
        system.concept = []
    system.concept.append(concept)

    return concept


def new_CodeSystemConceptProperty(concept: CodeSystemConcept, code: str, type: str, value: any) -> CodeSystemConceptProperty:
    """
    Set the appropriate value field on a CodeSystemConceptProperty based on type
    """
    if code is None or value is None or type is None:
        return None

    if len(code) == 0 or len(value) == 0 or len(type) == 0:
        return None

    if type == "string":
        prop = CodeSystemConceptProperty(code=code, valueString=str(value))
    elif type == "code":
        prop = CodeSystemConceptProperty(code=code, valueCode=str(value))
    elif type == "Coding":
#        prop.valueCoding = value
        raise NotImplementedError("Coding type is not implemented in this function.")
    elif type == "boolean":
        prop = CodeSystemConceptProperty(code=code, valueBoolean=bool(value))
    elif type == "integer":
        prop = CodeSystemConceptProperty(code=code, valueInteger=int(value))
    elif type == "decimal":
        prop = CodeSystemConceptProperty(code=code, valueDecimal=float(value))
    elif type == "dateTime":
        prop = CodeSystemConceptProperty(code=code, valueDateTime=value)

    # ensure we have the property list on the concept, and add the property
    if not concept.property:
        concept.property = []
    concept.property.append(prop)

    return prop

def is_file_fresh(filename: str, hours_old: int = 24) -> bool:
    """Check if a file exists and is newer than specified hours.
    
    Args:
        filename: Path to the file to check
        hours_old: Maximum age in hours (default 24)
        
    Returns:
        bool: True if file exists and is fresh, False otherwise
    """
    path = pathlib.Path(filename)
    if path.exists():
        file_age = time.time() - path.stat().st_mtime
        if file_age < hours_old * 3600:  # Convert hours to seconds
            print(f"Data file already exists at {filename} and is less than {hours_old} hours old. Skipping data fetch.")
            return True
    return False

def download_file(url: str, local_path: str) -> None:
    """Download a file from a URL and save it to a local path.
    
    Args:
        url: URL of the file to download
        local_path: Local path where the file will be saved
    """
    print(f"Downloading {url} to {local_path}...")
    response = requests.get(url)
    if response.status_code == 200:
        filename = local_path
        zip = False
        if url.endswith('.gz'):
            zip = True
        path = pathlib.Path(filename)
        path.write_bytes(response.content)

        if zip:
            # Decompress the file
            with gzip.open(path, 'rb') as f_in:
                target_path = pathlib.Path(local_path)
                target_path.write_bytes(f_in.read())

        print(f"Downloaded {url} successfully.")
    else:
        print(f"Failed to download {url}. Status code: {response.status_code}")
