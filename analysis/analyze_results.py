import json
import pandas as pd
import argparse
import os
import glob
import logging
from typing import Optional, List, Dict, Set, Any, Tuple
from itertools import product
from pathlib import Path

# --- Logging Setup (Minimal for now, can be expanded if needed) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Core Columns & Grouping Definitions ---
# Columns absolutely required for the current accuracy analysis
CORE_REQUIRED_COLUMNS: Set[str] = {'is_correct'}

class ResultsAnalyzer:
    """
    Handles loading, validating, and analyzing NLP experiment results,
    focusing on accuracy calculations with placeholders for future expansions.
    """

    def __init__(self, args: argparse.Namespace):
        self.input_pattern: str = args.input_pattern
        self.accuracy_metrics: list = args.accuracy_metrics
        self.confidence_metrics: list = args.confidence_metrics
        self.output_file_path: str = args.output_file_path
        self.confidence_to_csv: bool = args.confidence_to_csv
        self.output_path = Path(self.output_file_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.df: Optional[pd.DataFrame] = None

        # Dynamically determine all columns needed for configured accuracy groupings
        self.required_columns_for_accuracy: Set[str] = CORE_REQUIRED_COLUMNS.copy()
        if self.accuracy_metrics:
            self.accuracy_groupby_definitions = dict()
            for metric in self.accuracy_metrics:
                if metric != 'overall_accuracy':
                    col = metric.split('by_')[-1]
                    self.accuracy_groupby_definitions[metric] = [col]
                    self.required_columns_for_accuracy.update([col])
        if self.confidence_metrics:
            self.required_columns_for_accuracy.update({
                "question_id", "option_permutation", "ground_truth_answer"
            })
        logger.debug(f"Required columns for accuracy: {self.required_columns_for_accuracy}")

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
        assert self.df is not None and not self.df.empty, "DataFrame is not loaded or is empty. Cannot validate."

        missing_cols = self.required_columns_for_accuracy - set(self.df.columns)
        if missing_cols:
            logger.error(f"Missing required columns for accuracy analysis: {missing_cols}")
            return False
        return True

    def calculate_overall_accuracy(self) -> Optional[float]:
        """Calculates overall accuracy from the 'is_correct' column."""
        assert self.df is not None, "DataFrame must be loaded before calculating accuracy."
        assert 'is_correct' in self.df.columns, "is_correct column is required for accuracy calculation."

        # Ensure 'is_correct' is boolean or numeric for mean calculation; handle potential strings
        valid_scores = pd.to_numeric(self.df['is_correct'].dropna(), errors='coerce')

        return valid_scores.mean() if not valid_scores.empty else 0.0

    def calculate_grouped_accuracies(
        self,
        group_by_definitions: Dict[str, List[str]]
    ) -> Dict[str, Optional[Dict]]:
        """
        Calculates accuracies grouped by specified column sets.
        :param group_by_definitions: A dictionary where keys are analysis names
                                     and values are lists of columns to group by.
        """
        assert self.df is not None, "DataFrame must be loaded before calculating accuracy."
        assert 'is_correct' in self.df.columns, "is_correct column is required for accuracy calculation."

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

    def calculate_confidence(self, to_csv:bool=False) -> Optional[Dict[str, Any]]:
        """
        Placeholder for analyzing the relationship between model confidence and order bias.
        This would require a 'model_confidence' column and results from fluctuation/bias analysis.
        """
        assert self.df is not None, "DataFrame must be loaded before calculating confidence metrics."
        assert not self.df.empty, "DataFrame is empty. Cannot perform confidence analysis."
        assert 'question_id' in self.df.columns, "question_id column is required for confidence analysis."

        candidate_cols = {'subtask', 'model_name', 'input_format', 'language'}
        cols = list(candidate_cols.intersection(self.df.columns))
        unique_vals = [self.df[col].dropna().unique() for col in cols]

        results = dict()
        for combination in product(*unique_vals):
            condition = True
            key = {}
            for col, val in zip(cols, combination):
                condition &= (self.df[col] == val)
                key[col] = val
            df_group = self.df[condition]

            if df_group.empty:
                continue

            key_list = [v for v in key.values()]
            key_str = str(tuple(key_list))
            results[key_str] = {"count": len(df_group)}
            confidence = self.__calculate_confidence(df_group)
            if "confidence_high" in confidence:
                confidence_high = confidence["confidence_high"]
                results[key_str]["overall_confidence_high"] = confidence_high["confidence_high"].mean()
                results[key_str]["detailed_confidence_high"] = confidence_high["confidence_high"].to_dict()
                if to_csv:
                    suffix = "_".join([str(v) for v in key_list])
                    fn = f"results_summary/confidence_high_{suffix}.csv"
                    confidence_high.to_csv(fn, index=False)
                    logger.info(f"Confidence high metrics saved to CSV for {fn}")
            if "confidence_low" in confidence:
                confidence_low = confidence["confidence_low"]
                results[key_str]["avg_confidence_low"] = confidence_low.mean().to_dict()
                results[key_str]["detailed_confidence_low"] = confidence_low.to_dict()
                if to_csv:
                    suffix = "_".join([str(v) for v in key_list])
                    fn = f"results_summary/confidence_low_{suffix}.csv"
                    confidence_low.to_csv(fn, index=False)
                    logger.info(f"Confidence low metrics saved to CSV for {fn}")

        return results


    def __calculate_confidence(self, df:pd.DataFrame) -> Dict[str, Any]:
        # Get the position of the ground truth answer in the option permutation
        df = df.copy()
        df["correct_pos"] = df.apply(
            lambda r: r["option_permutation"].index(r["ground_truth_answer"]) + 1,
            axis=1
        )

        confidence = dict()

        if "confidence_high" in self.confidence_metrics:
            logger.info("High confidence analysis placeholder invoked.")
            acc_by_pos = df.groupby(["question_id", "correct_pos"])["is_correct"].mean()
            acc_by_pos = acc_by_pos.unstack("correct_pos").rename_axis(index=None, columns="correct_pos")
            acc_by_pos["confidence_high"] = acc_by_pos.std(axis=1)
            confidence["confidence_high"] = acc_by_pos

        if "confidence_low" in self.confidence_metrics:
            logger.info("Low confidence analysis placeholder invoked.")
            std_by_pos = df.groupby(["question_id", "correct_pos"])["is_correct"].std()
            std_by_pos = std_by_pos.unstack("correct_pos").rename_axis(index=None, columns="correct_pos")
            confidence["confidence_low"] = std_by_pos

        return confidence

    def generate_summary_report(
        self,
        accuracy_metrics: Optional[Dict[str, Any]],
        confidence_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates a dictionary summarizing all calculated metrics.
        Currently focuses on accuracy; will be expanded.
        """
        report = {}
        if self.accuracy_metrics:
            report["accuracy_metrics"] = accuracy_metrics
        if self.confidence_metrics:
            report["confidence_metrics"] = confidence_metrics

        # TODO: Add fluctuation_metrics to the report when implemented
        # "order_bias_metrics": self.calculate_fluctuation_metrics(),

        # Minimal logging of the report structure for now
        logger.info(f"Summary Report Keys: {list(report.keys())}")
        return report

    def save_report_to_file(self, report_data: Dict[str, Any]) -> None:
        """Saves the summary report to a JSON file."""
        try:
            with self.output_path.open('w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=4, default=str) # default=str for non-serializable types if any
            logger.info(f"Full analysis report saved to {self.output_path}")
        except Exception as e:
            logger.error(f"Failed to save report to {self.output_path}: {e}")

    def run_analysis(self) -> None:
        """Main analysis pipeline runner."""

        success_loading = self.load_data()
        success_validating = self.validate_data_for_accuracy()
        if not (success_loading and success_validating):
            logger.error("Analysis aborted due to data loading or validation issues.")
            return

        accuracy_summary = dict()
        logger.info("Calculating accuracy metrics...")
        if 'overall_accuracy' in self.accuracy_metrics:
            overall_accuracy = self.calculate_overall_accuracy()
            logger.info(f"Overall Accuracy: {overall_accuracy:.4f}" if overall_accuracy is not None else "Overall Accuracy: N/A")
            accuracy_summary['overall_accuracy'] = overall_accuracy
        grouped_accuracies = self.calculate_grouped_accuracies(self.accuracy_groupby_definitions)
        accuracy_summary['grouped_accuracies'] = grouped_accuracies
        confidence = self.calculate_confidence(self.confidence_to_csv)

        # TODO: Invoke and integrate other analysis components when they are implemented
        # E.g., fluctuation_metrics = self.calculate_fluctuation_metrics()

        final_report = self.generate_summary_report(accuracy_summary, confidence)
        self.save_report_to_file(final_report)

        logger.info("Accuracy analysis complete.")


def main():
    parser = argparse.ArgumentParser(description="Analyze NLP experiment results (Accuracy Focus).")

    parser.add_argument("input_pattern", help="Glob pattern for input JSONL files (e.g., 'results/*.jsonl')")

    parser.add_argument(
        "--accuracy_metrics", nargs='+', default=[
            'overall_accuracy',
            'by_subtask',
            'by_model_name',
            'by_input_format',
            'by_language',
        ],
        help="List of accuracy metrics to calculate (e.g., 'overall_accuracy', 'by_subtask').")

    parser.add_argument(
        "--confidence_metrics", nargs='+', default=[
            'confidence_high',
            'confidence_low'
        ],
        help="List of confidence metrics to calculate (e.g., 'confidence_high', 'confidence_low').")

    parser.add_argument(
        "--output_file_path",
        default="results_summary/accuracy_metrics.json",
        help="Path to save the summary of accuracy metrics."
    )

    parser.add_argument("--confidence_to_csv", action='store_true', help="Save confidence metrics to CSV format.")


    # TODO: Add arguments for other output files (e.g., fluctuation details) when those analyses are added.
    # parser.add_argument("--output_fluctuation_details_file", default="results_summary/fluctuation_details.csv")

    args = parser.parse_args()

    analyzer = ResultsAnalyzer(args)
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
