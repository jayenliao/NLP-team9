import json
import pandas as pd
import argparse
import os
import glob
import logging
from typing import Optional, List, Dict, Set, Any
from pathlib import Path

# --- Logging Setup (Minimal for now, can be expanded if needed) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Core Columns & Grouping Definitions ---
# Columns absolutely required for the current accuracy analysis
CORE_REQUIRED_COLUMNS: Set[str] = {'is_correct'}

# Definitions for grouped accuracy analyses.
# The key is a descriptive name for the analysis, value is a list of columns to group by.
# This can be expanded as more grouping dimensions (e.g., 'requested_output_format') are added.
ACCURACY_GROUPBY_DEFINITIONS: Dict[str, List[str]] = {
    'by_subtask': ['subtask'],
    'by_model': ['model_name'],
    'by_input_format': ['input_format'], # Current input format
    'by_language': ['language'],
    # TODO: Add 'by_requested_output_format' when that data field is available
    # 'by_input_output_format_pair': ['input_format', 'requested_output_format'],
}


class ResultsAnalyzer:
    """
    Handles loading, validating, and analyzing NLP experiment results,
    focusing on accuracy calculations with placeholders for future expansions.
    """

    def __init__(self, input_pattern: str):
        self.input_pattern: str = input_pattern
        self.df: Optional[pd.DataFrame] = None
        # Dynamically determine all columns needed for configured accuracy groupings
        self.required_columns_for_accuracy: Set[str] = CORE_REQUIRED_COLUMNS.copy()
        for cols in ACCURACY_GROUPBY_DEFINITIONS.values():
            self.required_columns_for_accuracy.update(cols)

    def load_data(self) -> bool:
        """Loads and combines all JSONL result files into a pandas DataFrame."""
        all_results: List[Dict[str, Any]] = []
        file_paths: List[str] = glob.glob(os.path.expanduser(self.input_pattern))

        if not file_paths:
            logger.warning(f"No files found for pattern: {self.input_pattern}")
            return False

        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            all_results.append(json.loads(line))
                        except json.JSONDecodeError:
                            # Minimal logging for conciseness, as per preference
                            logger.debug(f"JSON decode error in {file_path} (line skipped)")
            except Exception:
                logger.debug(f"Failed to read or process {file_path}")
                # Continue to next file if one fails, or return False if a stricter policy is needed
        
        if not all_results:
            logger.warning("No data loaded from any files.")
            self.df = pd.DataFrame()
            return False
            
        self.df = pd.DataFrame(all_results)
        logger.info(f"Successfully loaded {len(self.df)} records from {len(file_paths)} file(s).")
        return True

    def validate_data_for_accuracy(self) -> bool:
        """Validates that the DataFrame has columns required for accuracy analysis."""
        if self.df is None or self.df.empty:
            logger.error("DataFrame is not loaded or is empty. Cannot validate.")
            return False
        
        missing_cols = self.required_columns_for_accuracy - set(self.df.columns)
        if missing_cols:
            logger.error(f"Missing required columns for accuracy analysis: {missing_cols}")
            return False
        return True

    def calculate_overall_accuracy(self) -> Optional[float]:
        """Calculates overall accuracy from the 'is_correct' column."""
        if self.df is None or 'is_correct' not in self.df.columns:
            return None
        # Ensure 'is_correct' is boolean or numeric for mean calculation; handle potential strings
        valid_scores = pd.to_numeric(self.df['is_correct'], errors='coerce').dropna()
        return valid_scores.mean() if not valid_scores.empty else 0.0

    def calculate_grouped_accuracies(self, group_by_definitions: Dict[str, List[str]]) -> Dict[str, Optional[Dict]]:
        """
        Calculates accuracies grouped by specified column sets.
        :param group_by_definitions: A dictionary where keys are analysis names
                                     and values are lists of columns to group by.
        """
        if self.df is None:
            return {name: None for name in group_by_definitions}

        grouped_accuracies_report: Dict[str, Optional[Dict]] = {}
        for analysis_name, group_by_cols in group_by_definitions.items():
            if not all(col in self.df.columns for col in group_by_cols):
                logger.warning(f"Missing one or more grouping columns for '{analysis_name}': {group_by_cols}. Skipping.")
                grouped_accuracies_report[analysis_name] = None
                continue
            
            # Ensure 'is_correct' is numeric before grouping
            temp_df = self.df.copy()
            temp_df['is_correct'] = pd.to_numeric(temp_df['is_correct'], errors='coerce')
            valid_df = temp_df.dropna(subset=['is_correct'] + group_by_cols)

            if valid_df.empty:
                grouped_accuracies_report[analysis_name] = {}
                continue
                
            result_series = valid_df.groupby(group_by_cols)['is_correct'].mean()
            grouped_accuracies_report[analysis_name] = result_series.to_dict()
            
        return grouped_accuracies_report

    # --- Placeholder Sections for Future Expansion ---

    def calculate_fluctuation_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Placeholder for calculating fluctuation rates and other order bias metrics.
        This would require 'option_permutation' and 'model_choice_original_label' columns,
        and potentially grouping by 'question_id' and other relevant dimensions.
        Metrics like Fluctuation Rate, RSD, RStd, CKLD would be implemented here.
        """
        # TODO: Implement fluctuation analysis (Fluctuation Rate, RSD, RStd, CKLD).
        # Requires columns like 'question_id', 'option_permutation', 'model_choice_original_label'.
        # Example structure:
        # fluctuation_report = {
        #     'overall_fluctuation_rate': self._calculate_some_fluctuation(self.df, group_cols_overall),
        #     'fluctuation_by_input_format': self._calculate_some_fluctuation(self.df, group_cols_input_format, group_by=['input_format']),
        #     # ... other fluctuation metrics and groupings
        # }
        # logger.info("Fluctuation analysis placeholder invoked.")
        return None

    def analyze_confidence_vs_bias(self) -> Optional[Dict[str, Any]]:
        """
        Placeholder for analyzing the relationship between model confidence and order bias.
        This would require a 'model_confidence' column and results from fluctuation/bias analysis.
        """
        # TODO: Implement confidence vs. bias analysis.
        # Requires a 'model_confidence' column and fluctuation/bias metrics.
        # logger.info("Confidence vs. bias analysis placeholder invoked.")
        return None

    def generate_summary_report(self, accuracy_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a dictionary summarizing all calculated metrics.
        Currently focuses on accuracy; will be expanded.
        """
        report = {
            "accuracies": accuracy_metrics,
            # TODO: Add fluctuation_metrics to the report when implemented
            # "order_bias_metrics": self.calculate_fluctuation_metrics(),
            # TODO: Add confidence_analysis_summary to the report when implemented
            # "confidence_vs_bias_summary": self.analyze_confidence_vs_bias(),
        }
        # Minimal logging of the report structure for now
        logger.info(f"Summary Report Keys: {list(report.keys())}")
        return report

    def save_report_to_file(self, report_data: Dict[str, Any], output_file_path: str) -> None:
        """Saves the summary report to a JSON file."""
        output_path = Path(output_file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with output_path.open('w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=4, default=str) # default=str for non-serializable types if any
            logger.info(f"Full analysis report saved to {output_path}")
        except Exception:
            logger.debug(f"Error saving report to {output_path}")


    def run_analysis(self, output_metrics_file: str) -> None:
        """Main analysis pipeline runner."""
        if not self.load_data() or not self.validate_data_for_accuracy():
            logger.error("Analysis aborted due to data loading or validation issues.")
            return

        logger.info("Calculating accuracy metrics...")
        overall_accuracy = self.calculate_overall_accuracy()
        grouped_accuracies = self.calculate_grouped_accuracies(ACCURACY_GROUPBY_DEFINITIONS)

        accuracy_summary = {
            'overall_accuracy': overall_accuracy,
            'grouped_accuracies': grouped_accuracies
        }
        logger.info(f"Overall Accuracy: {overall_accuracy:.4f}" if overall_accuracy is not None else "Overall Accuracy: N/A")
        
        # TODO: Invoke and integrate other analysis components when they are implemented
        # E.g., fluctuation_metrics = self.calculate_fluctuation_metrics()
        # E.g., confidence_summary = self.analyze_confidence_vs_bias()

        final_report = self.generate_summary_report(accuracy_summary)
        self.save_report_to_file(final_report, output_metrics_file)
        
        logger.info("Accuracy analysis complete.")


def main():
    parser = argparse.ArgumentParser(description="Analyze NLP experiment results (Accuracy Focus).")
    parser.add_argument("input_pattern", 
                        help="Glob pattern for input JSONL files (e.g., 'results/*.jsonl')")
    parser.add_argument("--output_metrics_file", 
                        default="results_summary/accuracy_metrics.json",
                        help="Path to save the summary of accuracy metrics.")
    # TODO: Add arguments for other output files (e.g., fluctuation details) when those analyses are added.
    # parser.add_argument("--output_fluctuation_details_file", default="results_summary/fluctuation_details.csv")

    args = parser.parse_args()

    analyzer = ResultsAnalyzer(args.input_pattern)
    analyzer.run_analysis(args.output_metrics_file)

if __name__ == "__main__":
    main()