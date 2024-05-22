import os
import shutil
import logging
import colorlog
import sys
from collections import Counter
from difflib import SequenceMatcher


class FileManagerError(Exception):
    """Custom error for FileManager."""
    pass


class FileManager:
    def __init__(self, documents_folder, size_difference_threshold=0.5, similarity_ratio_threshold=0.85, similarity_skip_threshold=0.3):
        self.documents_folder = documents_folder
        self.size_difference_threshold = size_difference_threshold
        self.similarity_ratio_threshold = similarity_ratio_threshold
        self.similarity_skip_threshold = similarity_skip_threshold
        self.setup_logging()
        self.duplicated_folder = os.path.join(documents_folder, 'Duplicated')
        self.zip_folder = os.path.join(documents_folder, 'Zip')
        self.ensure_directories()

    def setup_logging(self):
        handler = colorlog.StreamHandler()
        format = "%(log_color)s%(asctime)s - %(levelname)s - %(message)s"
        formatter = colorlog.ColoredFormatter(format, datefmt='%Y-%m-%d %H:%M:%S',
                                              log_colors={
                                                  'DEBUG': 'cyan',
                                                  'INFO': 'green',
                                                  'WARNING': 'yellow',
                                                  'ERROR': 'red',
                                                  'CRITICAL': 'bold_red'
                                              })
        handler.setFormatter(formatter)
        self.logger = logging.getLogger('file_manager')
        self.logger.addHandler(handler)
        self.logger.addHandler(logging.FileHandler('file_manager.log'))

        # Set logger level according to the environment
        if os.environ.get('ENV') == 'production':
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.DEBUG)

    def ensure_directories(self):
        try:
            os.makedirs(self.duplicated_folder, exist_ok=True)
            os.makedirs(self.zip_folder, exist_ok=True)
            self.logger.info(f"Ensured directories: {self.duplicated_folder}, {self.zip_folder}")
        except OSError as e:
            raise FileManagerError(f"Can't ensure directories: {str(e)}") from e

    def move_file(self, src, dest_folder):
        try:
            shutil.move(src, dest_folder)
            self.logger.info(f"Moved file: {src} -> {dest_folder}")
        except (OSError, shutil.Error) as e:
            raise FileManagerError(f"Can't move file from {src} to {dest_folder}: {str(e)}") from e

    def read_file_content(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            with open(filepath, 'rb') as file:
                return file.read().decode('utf-8', errors='ignore')

    def tokenize(self, text):
        return text.split()

    def get_token_set(self, content):
        tokens = self.tokenize(content)
        return Counter(tokens)

    def compare_token_sets(self, set1, set2):
        common_tokens = sum((set1 & set2).values())
        total_tokens = sum((set1 | set2).values())
        return common_tokens / total_tokens

    def compare_filenames(self, name1, name2):
        return SequenceMatcher(None, name1, name2).ratio()

    def compare_and_move_files(self):
        try:
            files = [entry for entry in os.scandir(self.documents_folder) if entry.is_file()]
            self.logger.info(f"Files to compare: {len(files)} files found")
            i = 0
            while i < len(files):
                file1 = files[i]
                if file1 is None:
                    i += 1
                    continue
                file1_size = os.path.getsize(file1.path)

                # Check if file1 is a zip file
                if file1.name.endswith('.zip'):
                    self.move_file(file1.path, self.zip_folder)
                    files[i] = None
                    i += 1
                    continue

                self.logger.debug(f"Reading content of file1: {file1.name}")
                file1_content = self.read_file_content(file1.path)
                file1_token_set = self.get_token_set(file1_content)

                skip_file1 = False

                for j in range(i + 1, len(files)):
                    file2 = files[j]
                    if file2 is None:
                        continue
                    file2_size = os.path.getsize(file2.path)

                    # Skip comparison if file2 is a zip file
                    if file2.name.endswith('.zip'):
                        self.move_file(file2.path, self.zip_folder)
                        files[j] = None
                        continue

                    # Compare filenames
                    filename_similarity = self.compare_filenames(file1.name, file2.name)
                    self.logger.debug(f"Filename similarity between {file1.name} and {file2.name}: {filename_similarity:.2f}")

                    if filename_similarity >= 0.7:
                        self.move_file(file2.path, self.duplicated_folder)
                        files[j] = None
                        continue

                    if filename_similarity <= 0.3:
                        self.logger.debug(f"Skipping {file2.name} due to low filename similarity with {file1.name}")
                        file1 = file2
                        file1_size = file2_size
                        file1_content = self.read_file_content(file1.path)
                        file1_token_set = self.get_token_set(file1_content)
                        i = j
                        break

                    # Skip comparison if file sizes differ significantly
                    if abs(file1_size - file2_size) / max(file1_size, file2_size) > self.size_difference_threshold:
                        self.logger.debug(f"Skipping {file2.name} due to significant size difference with {file1.name}")
                        file1 = file2
                        file1_size = file2_size
                        file1_content = self.read_file_content(file1.path)
                        file1_token_set = self.get_token_set(file1_content)
                        i = j
                        break

                    self.logger.debug(f"Reading content of file2: {file2.name}")
                    file2_content = self.read_file_content(file2.path)
                    file2_token_set = self.get_token_set(file2_content)
                    similarity = self.compare_token_sets(file1_token_set, file2_token_set)
                    self.logger.debug(f"Similarity between {file1.name} and {file2.name}: {similarity:.2f}")

                    if similarity < self.similarity_skip_threshold:
                        self.logger.debug(f"Skipping {file2.name} due to low similarity with {file1.name}")
                        file1 = file2
                        file1_size = file2_size
                        file1_content = self.read_file_content(file1.path)
                        file1_token_set = self.get_token_set(file1_content)
                        i = j
                        break

                    if similarity > self.similarity_ratio_threshold:
                        if file1_size < file2_size:
                            self.move_file(file1.path, self.duplicated_folder)
                            files[i] = None
                            skip_file1 = True
                            break
                        else:
                            self.move_file(file2.path, self.duplicated_folder)
                            files[j] = None

                if not skip_file1:
                    i += 1
                else:
                    i += 1

        except OSError as e:
            raise FileManagerError(f"Can't read files from {self.documents_folder}: {str(e)}") from e


if __name__ == "__main__":
    if len(sys.argv) > 1:
        documents_folder = sys.argv[1]
    else:
        documents_folder = os.path.join(os.path.dirname(__file__), 'Documents')  # Default relative path

    try:
        manager = FileManager(documents_folder)
        manager.compare_and_move_files()
    except FileManagerError as e:
        print(f"FileManagerError occurred: {str(e)}", file=sys.stderr)
