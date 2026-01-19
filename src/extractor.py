import os
import pandas as pd
import chardet
import logging

logger = logging.getLogger(__name__)

def detect_encoding(file_path: str) -> str:
    """
    Detects the encoding of a file using chardet.
    Reads the first 100KB to guess.
    """
    try:
        with open(file_path, 'rb') as f:
            rawdata = f.read(100000)
        result = chardet.detect(rawdata)
        encoding = result['encoding']
        confidence = result['confidence']
        logger.info(f"Detected encoding: {encoding} with confidence {confidence}")
        
        # Fallback if confidence is low or None (default to utf-8 if similar)
        if not encoding:
            return 'utf-8'
        return encoding
    except Exception as e:
        logger.error(f"Error detecting encoding: {e}")
        return 'utf-8' # Fallback

def extract_csv(file_path: str) -> pd.DataFrame:
    """
    Reads a CSV file into a DataFrame, handling encoding automatically.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    encoding = detect_encoding(file_path)
    
    try:
        df = pd.read_csv(file_path, encoding=encoding)
        return df
    except UnicodeDecodeError:
        logger.warning(f"Failed with {encoding}, trying 'latin-1' as fallback.")
        return pd.read_csv(file_path, encoding='latin-1')
    except Exception as e:
        logger.error(f"Error extracting CSV: {e}")
        raise

def validate_columns(df: pd.DataFrame, required_columns: list) -> bool:
    """
    Checks if the dataframe contains the required columns.
    """
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        logger.error(f"Missing columns: {missing}")
        return False
    return True
