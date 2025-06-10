import os
import time
import requests
import gzip
import shutil

def is_file_fresh(filename: str, hours_old: int = 24) -> bool:
    """Check if a file exists and is newer than specified hours.
    
    Args:
        filename: Path to the file to check
        hours_old: Maximum age in hours (default 24)
        
    Returns:
        bool: True if file exists and is fresh, False otherwise
    """
    if os.path.exists(filename):
        file_age = time.time() - os.path.getmtime(filename)
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
            filename += '.gz'  # Append .gz if the URL indicates a gzipped file
        with open(filename, 'wb') as f:
            f.write(response.content)

        if zip:
            # Decompress the file
            with gzip.open(filename, 'rb') as f_in:
                with open(local_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

        print(f"Downloaded {url} successfully.")
    else:
        print(f"Failed to download {url}. Status code: {response.status_code}")
