"""
tmpfilehelper
"""

from pathlib import Path
import tempfile


class TmpFileHelper:
    """
    defines a TmpFileHelper
    """
    def __init__(self) -> None:
        self.tmp_files = []
        self.tmp_count = 0

    def get_generated_temp_files(self) -> list:
        """
        get all generated files.
        
        Returns:
        (list):
            the active temporary files
        """
        return self.tmp_files

    def generate_temp_file_name(self) -> Path:
        """
        generate a new temp-file.
        
        Returns:
        (Path):
            the path to the new file
        """
        tmp_file = Path(tempfile.NamedTemporaryFile(delete=False).name)
        self.tmp_files.append(tmp_file)
        self.tmp_count += 1
        return tmp_file
