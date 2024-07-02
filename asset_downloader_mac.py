import requests
import os
import sys
from tqdm import tqdm
import zipfile

ASSETZIP = "https://github.com/jake-drysdale/crate-dig/releases/download/assets/assets.zip"
ASSETZIP_NAME = os.path.expanduser("~/Library/Application Support/CrateDigAI/assets.zip")
DESTINATION = "assets"

def download_file(url, destination_name, progress_callback=None):
    try:
        if os.path.exists(destination_name):
            tqdm.write(f"File {destination_name} already exists on disk.")
            return

        response = requests.get(url, stream=True, timeout=1200)
        total_size = int(response.headers.get("content-length", 0))
        chunk_size = 1024 * 1024  # 1 MB chunks

        # Initialize progress bar with content-length
        progress_bar = tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            dynamic_ncols=True,
            desc=f"Downloading {destination_name}",
        )

        with open(destination_name, "wb") as f:
            for data in response.iter_content(chunk_size=chunk_size):
                f.write(data)
                progress_bar.update(len(data))
                if progress_callback:
                    progress_callback(progress_bar.n / total_size * 100)

        progress_bar.close()
    except Exception as e:
        tqdm.write(f"Error downloading/uploading {destination_name}: {str(e)}")
        raise e

def download_assets(destination, progress_callback=None):
    download_file(ASSETZIP, ASSETZIP_NAME, progress_callback)
    print("Extracting assets...")
    with zipfile.ZipFile(ASSETZIP_NAME, 'r') as zip_ref:
        zip_ref.extractall(destination)
    os.remove(ASSETZIP_NAME)

