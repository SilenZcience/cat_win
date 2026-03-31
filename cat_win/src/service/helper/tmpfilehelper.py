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
        with tempfile.NamedTemporaryFile(delete=False) as f:
            tmp_file = Path(f.name)
        self.tmp_files.append(tmp_file)
        return tmp_file
