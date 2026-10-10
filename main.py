"""Main Execution Pipeline for EV Charging Analytics.

Coordinates execution across:
- Data loading and schema validation
- Preprocessing and feature engineering
- Exploratory data analysis
- Aggregated demand analysis
- Demand forecasting pipeline
- Session-level anomaly detection
- Evaluation reporting and dashboard launch
"""

import argparse
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("EV_Charging_Analytics")


def parse_args():
    parser = argparse.ArgumentParser(description="EV Charging Analytics Pipeline")
    parser.add_argument(
        "--phase",
        type=str,
        default="verify",
        choices=["verify", "preprocess", "eda", "demand", "forecast", "anomaly", "all"],
        help="Pipeline phase to execute",
    )
    return parser.parse_args()


def run_preprocess():
    """Execute preprocessing pipeline and export clean session and hourly datasets."""
    from src.preprocessing import preprocess_dataset
    
    logger.info("Executing Phase 4 Preprocessing Pipeline...")
    session_df, hourly_df, report = preprocess_dataset(
        raw_filepath="data/raw/acn_caltech_5000.json",
        output_session_path="data/processed/cleaned_sessions.csv",
        output_hourly_path="data/processed/hourly_demand.csv",
    )
    logger.info(f"Preprocessing completed successfully. Sessions: {len(session_df)}, Hourly records: {len(hourly_df)}")
    return session_df, hourly_df, report


def run_eda(session_df=None, hourly_df=None):
    """Generate all 12 EDA figures and 5 empirical summary tables."""
    import pandas as pd
    from src.eda import generate_all_eda_figures, generate_summary_tables
    
    if session_df is None or hourly_df is None:
        sess_path = Path("data/processed/cleaned_sessions.csv")
        hr_path = Path("data/processed/hourly_demand.csv")
        if not sess_path.exists() or not hr_path.exists():
            session_df, hourly_df, _ = run_preprocess()
        else:
            logger.info("Loading existing processed datasets for EDA...")
            session_df = pd.read_csv(sess_path)
            hourly_df = pd.read_csv(hr_path)
            
    logger.info("Generating publication-quality figures (12 figures)...")
    fig_paths = generate_all_eda_figures(session_df, hourly_df, "outputs/figures")
    logger.info(f"Generated {len(fig_paths)} figures in outputs/figures/")
    
    logger.info("Generating empirical descriptive summary tables...")
    table_paths = generate_summary_tables(session_df, hourly_df, "outputs/tables")
    logger.info(f"Generated {len(table_paths)} tables in outputs/tables/")


def run_forecasting():
    """Execute Phase 5: Demand Forecasting Pipeline."""
    import pandas as pd
    from src.forecasting import (
        train_and_evaluate_forecasting_models,
        generate_forecasting_figures,
        perform_residual_analysis,
    )
    
    hr_path = Path("data/processed/hourly_demand.csv")
    if not hr_path.exists():
        logger.info("Hourly demand dataset not found. Running preprocessing first...")
        _, hourly_df, _ = run_preprocess()
    else:
        logger.info("Loading existing hourly demand dataset for forecasting...")
        hourly_df = pd.read_csv(hr_path)
        
    logger.info("Training and evaluating candidate forecasting models...")
    comp_df, artifacts, val_preds, test_preds = train_and_evaluate_forecasting_models(hourly_df)
    
    best_model = str(comp_df.iloc[0]["Model"])
    logger.info(f"Model Selection: Best performing model on Validation set is '{best_model}'.")
    
    logger.info("Generating publication-quality forecasting figures (7 figures)...")
    fig_paths = generate_forecasting_figures(test_preds, comp_df, "outputs/figures", best_model_name=best_model)
    logger.info(f"Generated {len(fig_paths)} forecasting figures in outputs/figures/")
    
    logger.info("Performing comprehensive residual analysis across demand strata...")
    res_df = perform_residual_analysis(test_preds, best_model, "outputs/tables")
    logger.info("Forecasting pipeline completed successfully.")


def run_anomaly_detection():
    """Execute Phase 6: Unsupervised Anomaly Detection Pipeline."""
    import pandas as pd
    from src.anomaly_detection import (
        execute_anomaly_detection_pipeline,
        generate_anomaly_figures,
    )
    
    sess_path = Path("data/processed/cleaned_sessions.csv")
    if not sess_path.exists():
        logger.info("Cleaned sessions dataset not found. Running preprocessing first...")
        session_df, _, _ = run_preprocess()
    else:
        logger.info("Loading existing cleaned sessions dataset for anomaly detection...")
        session_df = pd.read_csv(sess_path)
        
    logger.info("Executing unsupervised anomaly detection (Isolation Forest & LOF)...")
    results_df, report = execute_anomaly_detection_pipeline(session_df, contamination=0.03)
    logger.info(f"Anomaly Detection Report: {report}")
    
    logger.info("Generating publication-quality anomaly diagnostic figures (8 figures)...")
    fig_paths = generate_anomaly_figures(results_df, "outputs/figures")
    logger.info(f"Generated {len(fig_paths)} anomaly figures in outputs/figures/")
    logger.info("Anomaly detection pipeline completed successfully.")


def main():
    args = parse_args()
    logger.info(f"Initializing EV Charging Analytics System in '{args.phase}' mode...")
    
    # Verify environment and directories
    required_dirs = [
        Path("data/raw"),
        Path("data/processed"),
        Path("outputs/figures"),
        Path("outputs/tables"),
        Path("outputs/results"),
        Path("models"),
    ]
    for d in required_dirs:
        d.mkdir(parents=True, exist_ok=True)
        
    raw_file = Path("data/raw/acn_caltech_5000.json")
    if not raw_file.exists():
        logger.error(f"Raw dataset file missing: {raw_file}")
        sys.exit(1)
        
    logger.info(f"Verified project structure and raw dataset presence ({raw_file}).")
    
    if args.phase == "verify":
        logger.info("System architecture is operational.")
    elif args.phase == "preprocess":
        run_preprocess()
    elif args.phase == "eda":
        run_eda()
    elif args.phase == "forecast":
        run_forecasting()
    elif args.phase == "anomaly":
        run_anomaly_detection()
    else:
        logger.info(f"Phase '{args.phase}' is queued for subsequent execution phases.")


if __name__ == "__main__":
    main()
