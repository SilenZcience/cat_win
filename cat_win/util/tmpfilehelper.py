"""
tmpfilehelper
"""

import tempfile

class TmpFileHelper():
    """
    defines a TmpFileHelper
    """
    def __init__(self) -> None:
        self.tmp_files = []
        self.tmp_count = 0

    def get_generated_temp_files(self) -> list:
        """
        get all generated files.
        """
        return self.tmp_files

    def generate_temp_file_name(self) -> str:
        """
        generate a new temp-file.
        
        Returns:
        (str):
            the path to the new file
        """
        tmp_file = tempfile.NamedTemporaryFile(delete=False).name
        self.tmp_files.append(tmp_file)
        self.tmp_count += 1
        return tmp_file
