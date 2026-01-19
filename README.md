# FluxCLI - Sales ETL Automation Bot

FluxCLI is a robust, automated ETL (Extract, Transform, Load) pipeline designed to process daily sales data. It extracts data from CSV files, cleans and transforms it, loads valid records into a SQLite database, and sends execution reports via Email and Slack.

![Execution Report](assets/execution_report.png)

## Features

-   **Automated Extraction**: Auto-detects daily sales files (e.g., `sales_20240119.csv`).
-   **Data Validation**: rigorous data cleaning and validation (email formats, numeric values).
-   **Quarantine System**: Automatically isolates invalid rows into error reports for review.
-   **Database Integration**: Efficiently updates records in SQLite using UPSERT strategies.
-   **Notifications**: Sends detailed successful/failed reports to Email and Slack.
-   **CLI Interface**: Flexible command-line tool with options for auto-detection, dry-runs, and specific file processing.

## Project Structure

-   `etl.py`: Main CLI entry point.
-   `mock_data_gen.py`: Utility to generate test data.
-   `src/`: Core logic modules (Extractor, Transformer, Loader, Notifier).
-   `config/`: Configuration settings.
-   `data/`: Directory for input files and quarantine reports.
-   `logs/`: Execution logs.

## Setup

### Prerequisites

-   Python 3.10+
-   pip

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/BR4Y4NEXE/FluxCLI.git
    cd FluxCLI
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Configure Environment:
    -   Copy `.env.example` to `.env`:
        ```bash
        cp .env.example .env
        ```
    -   Open `.env` and fill in your details:
        ```properties
        # Database
        DB_PATH=sales_data.sqlite

        # Notifications
        ENABLE_NOTIFICATIONS=true
        SMTP_SERVER=smtp.gmail.com
        SMTP_PORT=587
        SMTP_USER=your_email@gmail.com
        SMTP_PASSWORD=your_app_password
        SLACK_WEBHOOK_URL=your_slack_webhook_url
        ```

## Usage

### 1. Generate Mock Data (For Testing)
Generate a sample CSV file with mixed valid and invalid data to test the pipeline:
```bash
python mock_data_gen.py
```
This creates a file in `data/input/sales_YYYYMMDD.csv`.

### 2. Run ETL Pipeline

**Automatic Mode (Detects today's file):**
```bash
python etl.py --auto
```

**Dry Run (Process without saving to DB or sending notifications):**
```bash
python etl.py --auto --dry-run
```

**Process a Specific File:**
```bash
python etl.py --file data/input/sales_20240119.csv
```

## Testing

Run the unit test suite:
```bash
pytest tests/
```

## License

This project is licensed under the MIT License.
