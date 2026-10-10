"""Data Loader Module.

Handles loading and schema validation of the raw ACN Caltech EV charging dataset
while preserving raw records intact without destructive modifications.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd

logger = logging.getLogger(__name__)

EXPECTED_TOP_LEVEL_FIELDS = {
    "_id",
    "clusterID",
    "connectionTime",
    "disconnectTime",
    "doneChargingTime",
    "kWhDelivered",
    "sessionID",
    "siteID",
    "spaceID",
    "stationID",
    "timezone",
    "userID",
    "userInputs",
}


def load_raw_json(filepath: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load raw JSON dataset from the specified file path.
    
    Args:
        filepath: Path to the JSON file.
        
    Returns:
        List of session dictionaries.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If JSON is invalid or empty.
    """
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"Raw dataset not found at {path}")
        
    logger.info(f"Loading raw dataset from {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    if not isinstance(data, list):
        raise ValueError(f"Expected list of records, got {type(data)}")
        
    if len(data) == 0:
        raise ValueError("Raw dataset is empty")
        
    logger.info(f"Successfully loaded {len(data)} raw sessions from {path}")
    return data


def validate_raw_schema(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate that top-level fields match the expected ACN schema.
    
    Args:
        data: List of raw session dictionaries.
        
    Returns:
        Dictionary containing validation report metadata.
    """
    if not data:
        raise ValueError("Cannot validate empty dataset")
        
    sample = data[0]
    present_fields = set(sample.keys())
    missing_fields = EXPECTED_TOP_LEVEL_FIELDS - present_fields
    
    all_fields_in_dataset = set()
    for item in data:
        all_fields_in_dataset.update(item.keys())
        
    report = {
        "total_records": len(data),
        "expected_fields": sorted(list(EXPECTED_TOP_LEVEL_FIELDS)),
        "present_fields": sorted(list(present_fields)),
        "missing_fields": sorted(list(missing_fields)),
        "all_distinct_fields": sorted(list(all_fields_in_dataset)),
        "is_valid": len(missing_fields) == 0,
    }
    
    if not report["is_valid"]:
        logger.warning(f"Schema validation warning: missing fields {missing_fields}")
    else:
        logger.info("Raw schema validation passed.")
        
    return report


def load_raw_dataset(filepath: Union[str, Path] = "data/raw/acn_caltech_5000.json") -> List[Dict[str, Any]]:
    """Convenience function to load and validate raw dataset.
    
    Args:
        filepath: Path to raw dataset. Defaults to 'data/raw/acn_caltech_5000.json'.
        
    Returns:
        List of verified raw session dictionaries.
    """
    data = load_raw_json(filepath)
    report = validate_raw_schema(data)
    if not report["is_valid"]:
        raise ValueError(f"Schema validation failed: {report['missing_fields']}")
    return data
