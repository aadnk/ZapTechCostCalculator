# Electric Vehicle Charging Cost Calculator

This tool allows you to calculate the cost of charging sessions for an electric vehicle, using the Zaptech API to fetch charging session data and another API to fetch electricity costs.

## Installation

### Step 1: Setup the Environment
Create a conda/virtual environment and install the requirements:

```bash
conda create --prefix ./.conda python=3.10
conda activate ./.conda
```
### Step 2: Install Dependencies
Then install the necessary Python packages listed in the `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
To extract the pricing of all charging sessions in a given time period, use the following command:

```bash
python app.py --from_date YYYY-MM-DD --to_date YYYY-MM-DD --output_file output.csv
```
Replace `YYYY-MM-DD` with the desired date range and `output.csv` with your desired output file name.

### Command Line Arguments

- `--from_date`: (Required) Start date (inclusive) in the format `YYYY-MM-DD`.
- `--to_date`: (Required) End date (exclusive) in the format `YYYY-MM-DD`.
- `--output_file`: (Required) Path to the output CSV file.
- `--secrets_file`: (Optional) Path to the secrets file. Default is "secrets.toml".
- `--username`: (Optional) Zaptech API username. Overrides secrets file.
- `--password`: (Optional) Zaptech API password. Overrides secrets file.

### Example
```bash
python app.py --from_date 2023-09-01 --to_date 2023-10-01 --output_file output.csv
```

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