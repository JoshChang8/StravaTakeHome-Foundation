import argparse
import sys
import json
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict, Any, Optional

class AnalyzeData:
    """
    Performs analysis on data from Strava's infrastructure logging
    """
    def __init__(self, data: List[Dict[str, Any]]) -> None:
        self.data = data
    
    def print_largest_indexes(self) -> None:
        """
        Prints the 5 largest indexes by size (GB)
        """
        print("\nPrinting largest indexes by storage size")
        sorted_largest_index = sorted(self.data, key=lambda x: x["size"], reverse=True)
        for index in sorted_largest_index[:5]:
            print(f"Index: {index['index']}")
            print(f"Size: {index['size']} GB")
    
    def print_most_shards(self) -> None:
        """
        Prints the 5 largest indexes by shard count 
        """
        print("\nPrinting largest indexes by shard count")
        sorted_largest_shard_count = sorted(self.data, key=lambda x: x["shards"], reverse=True)
        for index in sorted_largest_shard_count[:5]:
            print(f"Index: {index['index']}")
            print(f"Shards: {index['shards']}")
    
    def print_least_balanced(self) -> None:
        """
        Prints the 5 biggest offenders of shard count based on GB/shards. 
        Recommended shard count is 30GB/shard 
        """
        SHARD_SZ_GB = 30
        for index in self.data:
            index['balance_ratio'] = int(index['size'] / index['shards'])
            if index['size'] >= SHARD_SZ_GB: 
                index['rec_shard_count'] = int(index['size'] / SHARD_SZ_GB)
            elif 0 < index['size'] < SHARD_SZ_GB: # round up to 1 shard 
                index['rec_shard_count'] = 1
            else:
                index['rec_shard_count'] = 0
        
        sorted_least_balanced = sorted(self.data, key=lambda x: x["balance_ratio"], reverse=True)
        print("\nPrinting least balanced indexes")
        for index in sorted_least_balanced[:5]:
            print(f"Index: {index['index']}")
            print(f"Size: {index['size']} GB")
            print(f"Shards: {index['shards']}")
            print(f"Balance Ratio: {index['balance_ratio']}")
            print(f"Recommended shard count is {index['rec_shard_count']}")

def get_data_from_file(filename: str) -> Optional[List[Dict[str, Any]]]:
    """
    Reads data from JSON file in /testcases folder
    
    Args:
        filename(str): file path of JSON file
    
    Returns:
        List or None: returns list of index dicts or None if error occurs 
    """
    print("Getting data from JSON file")
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def get_data_from_server(endpoint: str, days: int) -> List[Dict[str, Any]]:
    """
    Gathers index data from API endpoint, each API call represents 1 day

    Args:
        endpoint(str): logging endpoint
        days(int): Number of prev days to add to data 
    
    Returns:
        list: list of index dicts retrieved from API
    """
    print("Getting data from server...")
    all_data = []
    # PST: "America/Los_Angeles"
    # MST: "America/Denver"
    today = datetime.now(ZoneInfo("America/Toronto")).date()

    for i in range(days):
        curr_date = today - timedelta(days=i)
        print(curr_date)
        year = curr_date.strftime("%Y")
        month = curr_date.strftime("%m")
        day = curr_date.strftime("%d")

        query = (f"https://{endpoint}/_cat/indices/*{year}*{month}*{day}?v&h=index,pri.store.size,pri&format=json&bytes=b")

        try:
            response = requests.get(query)
            daily_data = response.json()
            all_data.extend(daily_data)

        except requests.exceptions.RequestException as err:
            print(f"Failed to retrieve data for date: {year}/{month}/{day}: {err}")

    return all_data
      
def refine_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Cleans and converts index data 

    Args:
        data(list): list of index dicts 
    
    Returns:
        list: cleaned list of valid entries, incompatible entries are skipped 
    """
    refined = []
    errors = []
    for index in data:
        try:
            refined.append({
                "index": index["index"],
                "size": round(int(index["pri.store.size"]) / (1000**3), 2), # convert to GB
                "shards": int(index["pri"])
            })
        except Exception as e:
            errors.append(index)

    if errors:
        print(f"Indexes with errors: {errors}")

    return refined

def main():
    # Parse CLI args 
    parser = argparse.ArgumentParser(description="Process index data.")
    parser.add_argument("--endpoint", type=str, default="",
                        help="Logging endpoint")
    parser.add_argument("--debug", action="store_true",
                        help="Debug flag used to run locally")
    parser.add_argument("--days", type=int, default=7,
                        help="Number of days of data to parse")
    args = parser.parse_args()
    data = None

    # read from either file (--debug) or API 
    if args.debug:
        # json file: indexes.json, example-empty.json, example-invalid.json, example-corrupt.json
        raw_data = get_data_from_file("testcases/example-in.json")
        if raw_data is None:
            sys.exit("Error reading data from file.")
        elif len(raw_data) == 0:
            print("JSON file contains no entries.")
    else:
        try:
            raw_data = get_data_from_server(args.endpoint, args.days)
        except Exception as err:
            sys.exit("Error reading data from API endpoint. Error: " + str(err))
    
    data = refine_data(raw_data)

    if data:
        analyze_data = AnalyzeData(data)
        analyze_data.print_largest_indexes()
        analyze_data.print_most_shards()
        analyze_data.print_least_balanced()
    else:
        print("Data could not be analyzed.")

if __name__ == '__main__':
    main()
