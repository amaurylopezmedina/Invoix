import json
import os
import shutil
from pathlib import Path

from fm.FImportSM import *

if __name__ == "__main__":
    # Specify the directory to organize
    source_directory = os.path.join(os.path.abspath(os.sep), "XMLValidar", "AR")
    while True:
        organize_files(source_directory)
