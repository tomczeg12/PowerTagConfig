import pandas as pd
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

class File:
    """
    Handles operations on a file containing data about PowerTags,
    including loading data, retrieving specific information, and updating the file.
    """

    def __init__(self, file_path: str) -> None:
        """
        Initializes the File object with a path to the data file.

        :param file_path: The path to the CSV file.
        """
        self.file_path = file_path
        self.all_data = None  # This will hold the DataFrame after loading

    def check_data_loaded(self) -> bool:
        """
        Checks if data is loaded.

        :return: True if data is loaded, False otherwise.
        """
        if self.all_data is not None:
            return True
        logging.warning("No data loaded to operate on.")
        return False

    def load_data(self) -> Optional[List[Tuple]]:
        """
        Reads the data in the 'Name', 'RF ID', 'Fuse' columns from the file.

        :return: List of tuples containing the data, or None if an error occurred.
        """
        required_columns = ['Name', 'RF ID', 'Fuse']
        try:
            self.all_data = pd.read_csv(self.file_path, usecols=required_columns)
            if len(self.all_data.columns) != len(required_columns):
                logging.critical("Error: Required columns (Name, RF ID, Fuse) not found in the file.")
                return None
            data_tuples = [tuple(x) for x in self.all_data.to_numpy()]
            return data_tuples
        except FileNotFoundError:
            logging.critical(f"File not found at the specified path: {self.file_path}")
        except pd.errors.EmptyDataError:
            logging.critical(f"Error: The file at {self.file_path} is empty.")
        except pd.errors.ParserError:
            logging.critical(f"Error: Unable to parse the file at {self.file_path}.")
        except Exception as e:
            logging.critical(f"An unexpected error occurred: {type(e).__name__}, {e}")

    def get_information(self, rfid: str) -> Tuple[str, str]:
        """
        Retrieves the Name and Fuse based on the provided RFID.

        :param rfid: RFID code of the PowerTag.
        :return: Tuple containing the Name and Fuse, or empty strings if not found.
        """
        if not self.check_data_loaded():
            return '', ''

        row = self.all_data[self.all_data['RF ID'] == rfid]
        if not row.empty:
            logging.info(f"Data for PowerTag with RFID: {rfid} found.")
            return row.iloc[0]['Name'], row.iloc[0]['Fuse']

        logging.warning(f"PowerTag with RFID: {rfid} not found.")
        return '', ''

    def save_data(self, filename: str = "PowerTags_checked.csv") -> None:
        """
        Saves the DataFrame to a CSV file.

        :param filename: Name of the file to save the data.
        """
        if self.check_data_loaded():
            self.all_data.to_csv(filename, index=False)
            logging.info(f"Data successfully saved to {filename}.")

    def mark_mounted(self, name: str, new_val: str) -> None:
        """
        Marks a PowerTag as mounted by updating the 'Mounted' column.

        :param name: Name of the PowerTag.
        :param new_val: Value to update in the 'Mounted' column.
        """
        if self.check_data_loaded():
            self.all_data.loc[self.all_data['Name'] == name, 'Mounted'] = new_val
            logging.info(f"PowerTag '{name}' marked as {new_val}.")

    def mark_correct_values(self, name: str, new_val: str) -> None:
        """
        Marks the 'Issues' column with a new value for a specified PowerTag.
        -1 - Current flow needs to be change; 0 - Electrical or other problem to check by engineer, 1 - readings are OK

        :param name: Name of the PowerTag.
        :param new_val: Value to set in the 'Issues' column.
        """
        if self.check_data_loaded():
            self.all_data.loc[self.all_data['Name'] == name, 'Issues'] = new_val
            logging.info(f"PowerTag '{name}' readings marked as {new_val}.")
