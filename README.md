# TravelTime/Google comparison tool

This tool is designed to compare the travel times fetched from 
[Google Maps Directions API](https://developers.google.com/maps/documentation/directions/get-directions) 
and [TravelTime Routes API](https://docs.traveltime.com/api/reference/routes).

## Features

- Fetch travel times from Google Maps and TravelTime in parallel, for provided origin/destination pairs and a set 
    of departure times.
- Departure times are calculated based on user provided start time, end time and interval.  
- Analyze the differences between the results and print out the 90%, 95% and 99% percentiles of worst absolute and relative errors.

## Prerequisites

The tool requires Python 3.8+ installed on your system. You can download it from [here](https://www.python.org/downloads/).

## Installation

Clone the repository:
```bash
git clone https://github.com/traveltime-dev/google-travel-time-comparison.git
cd google-travel-time-comparison
```

Create a new virtual environment with a chosen name (here, we'll name it env):
```bash
python -m venv env
```

Activate the virtual environment:
```bash
source env/bin/activate
```

Install the project dependencies:
```bash
pip install -r requirements.txt
```

## Setup
Set up environment variables for the APIs:
For Google Maps:

```bash
export GOOGLE_API_KEY=[Your Google Maps API Key]
```

For TravelTime:
```bash
export TRAVELTIME_APP_ID=[Your TravelTime App ID]
export TRAVELTIME_API_KEY=[Your TravelTime API Key]
```

## Usage
Run the tool:
```bash
python main.py --input [Input CSV file path] --output [Output CSV file path] --date [Date (YYYY-MM-DD)] \ 
               --start-time [Start time (HH:MM)] --end-time [End time (HH:MM)] --interval [Interval in minutes] \ 
               --time-zone-id [Time zone ID] 
```
Required arguments:
- `--input [Input CSV file path]`: Path to the input file. Input file is required to have a header row and at least one 
    row with data, with two columns: `origin` and `destination`.
    The values in the columns must be latitude and longitude pairs, separated 
    by comma and enclosed in double quotes. For example: `"51.5074,-0.1278"`. Columns must be separated by comma as well.
    Look at the `examples` directory for examples. 
- `--output [Output CSV file path]`: Path to the output file. It will contain the gathered travel times. 
  See the details in the [Output section](#output)
- `--date [Date (YYYY-MM-DD)]`: date on which the travel times are gathered. Use a future date, as Google API returns
  errors for past dates (and times). Take into account the time needed to collect the data for provided input.
- `--start-time [Start time (HH:MM)]`: start time in `HH:MM` format, used for calculation of departure times.
  See [Calculating departure times](#calculating-departure-times)
- `--end-time [End time (HH:MM)]`: end time in `HH:MM` format, used for calculation of departure times.
  See [Calculating departure times](#calculating-departure-times)
- `--interval [Interval in minutes]`: interval in minutes, used for calculation of departure times. 
   See [Calculating departure times](#calculating-departure-times)
- `--time-zone-id [Time zone ID]`: non-abbreviated time zone identifier in which the time values are specified. 
  For example: `Europe/London`. For more information, see [here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).



Optional arguments:
- `--mode [Mode]`: Mode of transportation(`driving` or `public_transport`). Default is `driving`.
- `--google-max-rpm [int]`: Set max number of parallel requests sent to Google API per minute. Default is 600. 
  It is enforced on per-second basis, to avoid bursts.
- `--traveltime-max-rpm [int]`: Set max number of parallel requests sent to TravelTime API per minute. Default is 600.
  It is enforced on per-second basis, to avoid bursts.
- `--skip-data-gathering`: Skip data gathering and read gathered travel times from input file.

Example:

```bash
    python main.py --input uk.csv --output output.csv --date 2023-09-20 --start-time 07:00 --end-time 20:00 --interval 180 --time-zone-id "Europe/London"
```

## Calculating departure times
Script will collect travel times on the given day for departure times between provided start-time and end-time, with the
given interval. The start-time and end-time are in principle inclusive, however if the time window is not exactly divisible by the 
given interval, the end-time will not be included. For example, if you set the start-time to 08:00, end-time to 20:00 
and interval to 240, the script will sample both APIs for departure times 08:00, 12:00, 16:00 and 20:00 (end-time 
included). But for interval equal to 300, the script will sample APIs for departure times 08:00, 13:00 and 18:00 (end-time 
is not included).

## Output
After the successful execution, the script prints out the 95% percentile of worst absolute and relative errors. E.g. if
the 95% percentile absolute error is 250 seconds, it means that among all the gathered results, 95% of travel times from 
TravelTime API is further apart from the equivalent Google API result than 250s. 

You can also check the output file for the detailed results. 
The output file will contain the `origin` and `destination` columns from input file, with additional 7 columns: 
  - `departure_time`: departure time in `YYYY-MM-DD HH:MM:SS±HHMM` format, calculated from the start-time, end-time and interval.
    It includes date, time and timezone offset.
  - `google_travel_time`: travel time gathered from Google Directions API in seconds
  - `google_distance`: distance gathered from Google Directions API in meters
  - `traveltime_travel_time`: travel time gathered from TravelTime API in seconds
  - `traveltime_distance`: distance gathered from TravelTime API in meters
  - `absolute_error`: absolute error between Google and TravelTime travel times in seconds
  - `relative_error`: relative error between Google and TravelTime travel times in percent, relative to Google result.

### Sample output
```csv
origin,destination,departure_time,google_time,google_distance,traveltime_time,traveltime_distance,absolute_error,relative_error
"52.18328265122799, 0.12210601890895814","52.21895534832237, 0.14567620275439855",07:00:00,663.0,5501.0,1112.0,5414.0,449.0,67.72247360482655
"52.18328265122799, 0.12210601890895814","52.21895534832237, 0.14567620275439855",10:00:00,798.0,5501.0,943.0,5414.0,145.0,18.170426065162907
"52.18328265122799, 0.12210601890895814","52.21895534832237, 0.14567620275439855",13:00:00,818.0,5501.0,943.0,5414.0,125.0,15.28117359413203
...
```

## License
This project is licensed under MIT License. For more details, see the LICENSE file.
