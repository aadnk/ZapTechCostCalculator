# Electric Vehicle Charging Cost Calculator

This tool allows you to calculate the cost of charging sessions for an electric vehicle, using the Zaptech API to fetch charging session data and the hvakosterstrommen.no API to fetch electricity costs.

## Installation

### Step 1: Setup the Environment
Create a conda/virtual environment and install the requirements:

```bash
conda create --prefix ./.conda python=3.10
conda activate ./.conda
```
Or use any other preferred method for creating a virtual environment.

### Step 2: Install Dependencies
Then install the necessary Python packages listed in the `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Binary Executable

You can also download `app.py` as a binary for Windows. Extract the zip file and run `app.exe` from the command line:

```bat
app.exe --from_date YYYY-MM-DD --to_date YYYY-MM-DD --price_area NO2 -output_file output.csv
```

## Usage

### Basic Usage
To extract the pricing of all charging sessions in a given time period, use the following command:

```bash
python app.py --from_date YYYY-MM-DD --to_date YYYY-MM-DD --price_area NO2 -output_file output.csv
```
Replace `YYYY-MM-DD` with the desired date range and `output.csv` with your desired output file name.

### Command Line Arguments

- `--from_date`: (Required) Start date (inclusive) in the format `YYYY-MM-DD`.
- `--to_date`: (Required) End date (exclusive) in the format `YYYY-MM-DD`.
- `--output_file`: (Required) Path to the output CSV file.
- `--secrets_file`: (Optional) Path to the secrets file. Default is "secrets.toml".
- `--username`: (Optional) Zaptech API username. Overrides secrets file.
- `--password`: (Optional) Zaptech API password. Overrides secrets file.
- `--price_area`: (Optional) Price area to use for electricity cost. Default is "NO2". Can be "N01" to "N5".
- `--low_net_usage_fee`: (Optional) Net usage fee for night time and weekends. Default is 0.2259 NOK/kWh.
- `--high_net_usage_fee`: (Optional) Net usage fee for day time. Default is 0.3059 NOK/kWh.

### Pricing areas

The following pricing areas can be used for the `--price_area` argument (NO for Norway, 1 - 5 for the different regions):

- `NO1`: Oslo / Øst-Norge
- `NO2`: Kristiansand / Sør-Norge
- `NO3`: Trondheim / Midt-Norge
- `NO4`: Tromsø / Nord-Norge
- `NO5`: Bergen / Vest-Norge

### Example
```bash
python app.py --from_date 2023-09-01 --to_date 2023-10-01 --price_area NO2 --output_file output.csv
```

#### Output
The output CSV file will contain the following columns:
```csv
SessionId,Timestamp,Energy,EnergyUsageFee,NetUsageFee,EnergyCost,NetUsageCost,TotalCostNoVat,TotalCostWithVAT,CostCurrency
7bf9fd8c-769c-4503-bf74-d6c0e32f6bac,2023-09-29 23:00:00+00:00,1.4949999999998909,0.00034,0.33772049999997533,0.000508299999999963,0.33772049999997533,0.3382287999999753,0.42278599999996913,NOK
7bf9fd8c-769c-4503-bf74-d6c0e32f6bac,2023-09-30 00:00:00+00:00,2.5270000000000437,0.00011,0.5708493000000099,0.0002779700000000048,0.5708493000000099,0.5711272700000098,0.7139090875000123,NOK
# etc.
```
To find the total cost of all charging sessions in the output file, sum the `TotalCostWithVAT` column.

## Authentication

The tool supports three methods for providing the Zaptech API username and password:

### Method 1: Environment Variables
Set your Zaptech API credentials as environment variables. Replace `your_username` and `your_password` with your actual credentials.
```bash
export ZAPTECH_USERNAME='your_username'
export ZAPTECH_PASSWORD='your_password'
```

### Method 2: Secrets File
Store your Zaptech API credentials in a secrets file (default is `secrets.toml`), formatted as follows:

```toml
[zaptech]
username = "your_username"
password = "your_password"
```
If your secrets file has a different name or is located in a different directory, use the `--secrets_file` argument to specify its path.

### Method 3: Command Line Arguments
Directly provide your Zaptech API credentials when running the script using `--username` and `--password` arguments:

```bash
python app.py --from_date 2023-09-01 --to_date 2023-10-01 --output_file output.csv --username your_username --password your_password
```

**Note:** If credentials are provided using multiple methods, the priority order is: 
1. Command Line Arguments
2. Secrets File
3. Environment Variables