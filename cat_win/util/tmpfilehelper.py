from tempfile import NamedTemporaryFile


class TmpFileHelper():
    def __init__(self) -> None:
        self.tmp_files = []

    def get_generated_temp_files(self) -> list:
        return self.tmp_files

    def generate_temp_file_name(self) -> str:
        tmp_file = NamedTemporaryFile(delete=False).name
        self.tmp_files.append(tmp_file)
        return tmp_file
