import argparse
import logging
import os
import sys
import datetime
import time
from config.settings import settings
from src import extractor, transformer, loader, notifier

# Setup Logging
logging.basicConfig(
    level=settings.app.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.app.log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ETL_CLI")

def main():
    parser = argparse.ArgumentParser(description="Sales ETL Automation Bot")
    parser.add_argument("--file", help="Path to specific CSV file")
    parser.add_argument("--auto", action="store_true", help="Auto-detect today's file")
    parser.add_argument("--dry-run", action="store_true", help="Process without DB writes or notifications")
    
    args = parser.parse_args()
    
    # 1. Determine Input File
    file_path = args.file
    if args.auto:
        today = datetime.date.today().strftime("%Y%m%d")
        expected_filename = f"sales_{today}.csv"
        found_path = os.path.join(settings.app.input_dir, expected_filename)
        if os.path.exists(found_path):
            file_path = found_path
        else:
            logger.error(f"Auto-detection failed: {found_path} not found.")
            sys.exit(1)
            
    if not file_path:
        parser.print_help()
        sys.exit(1)
        
    start_time = time.time()
    logger.info(f"Starting ETL for {file_path}")
    
    try:
        # 2. Extract
        df = extractor.extract_csv(file_path)
        total_read = len(df)
        logger.info(f"Extract: {total_read} rows read")
        
        # 3. Transform
        result = transformer.transform(df)
        logger.info(f"Transform: {result.total_valid} valid, {result.total_rejected} rejected")
        
        # 4. Handle Quarantine
        if not result.rejected_df.empty:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            q_filename = f"errors_{timestamp}.csv"
            q_path = os.path.join(settings.app.quarantine_dir, q_filename)
            result.rejected_df.to_csv(q_path, index=False)
            logger.info(f"Quarantined {len(result.rejected_df)} rows to {q_path}")
            
        # 5. Load (if not dry-run)
        inserts, updates = 0, 0
        if not args.dry_run:
            data_loader = loader.DataLoader()
            data_loader.init_db()
            inserts, updates = data_loader.load_data(result.valid_df)
            logger.info(f"Load: {inserts} inserted, {updates} updated")
        else:
            logger.info("Dry run: Skipping DB load")
            
        duration = round(time.time() - start_time, 2)
        status = "SUCCESS"
        logger.info(f"ETL COMPLETED SUCCESSFULLY in {duration}s")
        
        # 6. Notify
        summary = {
            "status": status,
            "duration": duration,
            "file_name": os.path.basename(file_path),
            "total_read": total_read,
            "total_valid": result.total_valid,
            "total_rejected": result.total_rejected,
            "db_inserts": inserts,
            "db_updates": updates
        }
        
        if not args.dry_run:
            notif = notifier.Notifier()
            notif.send_report(summary)
            
    except Exception as e:
        logger.error(f"ETL Failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
