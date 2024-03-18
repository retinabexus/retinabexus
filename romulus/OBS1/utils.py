from csv import DictWriter

#################################################################################################

def writeCSV(packet: list, filename: str, fieldnames: list):
    """
    Function to save telemetry data into a csv file.

        Args: 
        - Received packet (splitted)
        - Path of the csv file
        - List of entries in the dataset
    """
    # Store new data:
    newData = {field: packet[i] for i, field in enumerate(fieldnames)}
    # Append data to the csv file: 
    with open(filename, 'a') as csvFile: DictWriter(csvFile, fieldnames=fieldnames).writerow(newData)

#################################################################################################