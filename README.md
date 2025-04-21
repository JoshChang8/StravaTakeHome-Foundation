# Strava Logging Analysis Tool 👟
This Python script analyzes Strava’s logging data by evaluating storage sizes, shard counts, and shard balance ratios. It supports both local JSON files and API endpoints.

## My Strava! 🏃‍♂️ 
<p align="center">
  <img src="photos/strava_art_time.png" alt="Yosemite National Park" width="400"/>
  <img src="photos/strava_art_route.png" alt="Squamish, BC" width="400"/>
</p>

<h3 align="center">
  <a href="https://strava.app.link/xzHTX3Y9xSb"><strong>Check out my Strava!</strong></a>
</h3>

## Analysis Overview 📊 
1. Top 5 Largest Indexes by Size 
  - Displays index names sorted by total size (GB)
2. Top 5 Indexes by Shard Count 
  - Displays index names sorted by the number of shards
3. Top 5 Least Balance Indexes 
  - Shows indexes storing too much data by shard (balance ratio)
  - Recommends new shard counts based on 30GB/shard

## Comparison with Output Example 🔍
The output of the script closely matches the `example-out.txt` file provided. To ensure my output followed the output file, I made it following adjustments:
- Size Conversion: converted the `pri.store.size` (bytes) to GB by divided by 1000^3 and rounding to 2 decimal places 
- Balance Ratio: calculated as ‘size/shards’ and truncated to an integer to match the sample output
- Recommended Shard Count: Based on the convention of 30GB/shard, also truncated to an integer

### Data Inconsistencies 
The example output does not consistently apply the same rounding rules. We can see that the secluded index balance ratio is truncated: 
```
Index: secluded
Size: 689.54 GB
Shards: 1
Balance Ratio: 689
```
However, the oblivion index balance ratio is rounded up:
```
Index: oblivion
Size: 537.62 GB
Shards: 7
Balance Ratio: 77
Note: 537.62/7 = 76.80, which should be 76 if truncated
```
I decided to implement an integer truncation for both the balance ratio and shard count, providing the same output for all indexes except for the `oblivion` index. 

## Test Cases ✅ 
To ensure correctness, I created several JSON test files to see how my script handles edge cases and error handling. All JSON test files are located in the `/testcases` folder. 
| Test File  | Description |
| ------------- | ------------- |
| `example-in.json`  | Valid output used to match example-out.txt file   |
| `example-empty.json`  | Tests how the script handles an empty input array []  |
| `example-invalid.json`  | Contains entries with missing key and value types   |
| `example-corrupt.json`  | Corrupt JSON object to simulate parsing error  |

## Run the Script ⚙️
### Run Locally with a JSON file (Debug Mode)
```
python infra-logging.py --debug
```
Uses the `testcases/example-in.json` by default. The file can be changed from the Python script in the main function. 
### Run with the API Input
```
python infra-logging.py --endpoint <ENDPOINT> --days 3
```
This queries data from the past N days (e.g., 3 days) and formats the date using the Toronto timezone. Responses are fetched daily with index stats and are aggregated into a single data list with the following API format:
```
https://<ENDPOINT>/_cat/indices/*<YYYY>*<MM>*<DD>?v&h=index,pri.store.size,pri&format=json&bytes=b
```
