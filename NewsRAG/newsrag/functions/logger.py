import logging
import json
from datetime import datetime

def log_item_id(item_id, chunk_no, chunk_id, log_file_path):
    # Configure the logging
    logging.basicConfig(filename=log_file_path, level=logging.INFO)

    log_data = {
        'timestamp': datetime.now().isoformat(),
        'level': 'VectorDB_update',
        'record_ID': item_id,
        'chunk_no' : chunk_no,
        'chunk_id' : chunk_id
    }
    logging.info(json.dumps(log_data))

def log_record_id_checker(file_path):
    # Initialize an empty list to store record_ID values
    record_ids = []
    # Open the file for reading
    with open(file_path, 'r') as file:
        # Iterate over each line in the file
        for line in file:
            if "INFO:root" in line:
                # Find the position of the JSON string within the log line
                start_pos = line.find("{")
                end_pos = line.rfind("}") + 1
                json_str = line[start_pos:end_pos]
                # Parse the JSON string to a dictionary
                log_data = json.loads(json_str)
                # Extract the record_ID and add it to the list
                record_id_set = log_data['record_ID']
                # Convert set to list and get the first element
                # record_id = list(record_id_set)[0]
                record_ids.append(record_id_set)
    return record_ids
# Print the list of record_ID values