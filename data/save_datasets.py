import datasets
import os
import pickle
import logging
from categories import categories, subcategories

# basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

script_dir = os.path.dirname(__file__)

def standardize_data_item(row: dict, language: str, index: int) -> dict | None:
    """Standardizes a row from MMLU or MMMLU datasets."""
    try:
        if language == 'en':
            std_item = {
                'id': row.get('id', f"en_{index}"),
                'question': row['question'],
                'choices': list(row['choices']),
                'answer_label': chr(ord('A') + row['answer']),
                'subject': row['subject']
            }
            if len(std_item['choices']) != 4:
                 logging.warning(f"[en] Row index {index} has incorrect choice count. Skipping.")
                 return None
        elif language == 'fr':
            std_item = {
                'id': row.get('Unnamed: 0', f"fr_{index}"),
                'question': row['Question'],
                'choices': [row['A'], row['B'], row['C'], row['D']],
                'answer_label': row['Answer'].upper().strip(),
                'subject': row['Subject']
            }
            if std_item['answer_label'] not in ['A', 'B', 'C', 'D']:
                 logging.warning(f"[fr] Row index {index} has invalid Answer label. Skipping.")
                 return None
        else:
            logging.error(f"Unsupported language '{language}'.")
            return None
        return std_item
    except KeyError as e:
        logging.error(f"Missing key '{e}' in row for lang '{language}' at index {index}. Skipping.")
        return None
    except Exception as e:
        logging.error(f"Error standardizing row lang '{language}' index {index}: {e}. Skipping.")
        return None

def save_datasets():
    """Loads, filters, standardizes, and saves MMLU/MMMLU datasets."""
    logging.info("Loading original datasets...")
    try:
        ds_en = datasets.load_dataset("cais/mmlu", "all", split="test")
        ds_fr = datasets.load_dataset("openai/MMMLU", "FR_FR", split="test")
        logging.info("Datasets loaded.")
    except Exception as e:
        logging.error(f"Failed to load datasets: {e}")
        return

    selected_categories = []
    for v in categories.values():
        selected_categories.extend(v)

    selected_subcategories = {}
    logging.info("Selecting subcategories...")
    temp_selected_categories = list(selected_categories) # Copy to modify while iterating
    for k, v in subcategories.items():
        category = v[0]
        if category in temp_selected_categories:
            selected_subcategories[category] = k
            temp_selected_categories.remove(category)
        if not temp_selected_categories:
            break
    logging.info(f"Selected subcategories: {list(selected_subcategories.values())}")

    logging.info("Filtering, standardizing, and collecting data...")
    ds_standardized = {}
    processed_count = {'en': 0, 'fr': 0}
    skipped_count = {'en': 0, 'fr': 0}

    for i, subcategory in enumerate(selected_subcategories.values()):
        logging.info(f"Processing subtask: {subcategory} ({i+1}/{len(selected_subcategories)})")
        ds_standardized[subcategory] = {"en": [], "fr": []}

        # Process English
        try:
            en_filtered = ds_en.filter(lambda x: x["subject"] == subcategory).select(range(100))
            for idx, row in enumerate(en_filtered):
                std_item = standardize_data_item(row, 'en', idx)
                if std_item:
                    ds_standardized[subcategory]["en"].append(std_item)
                    processed_count['en'] += 1
                else:
                     skipped_count['en'] += 1
        except Exception as e:
             logging.error(f"Error processing EN data for {subcategory}: {e}")

        # Process French
        try:
            fr_filtered = ds_fr.filter(lambda x: x["Subject"] == subcategory).select(range(100))
            for idx, row in enumerate(fr_filtered):
                std_item = standardize_data_item(row, 'fr', idx)
                if std_item:
                    ds_standardized[subcategory]["fr"].append(std_item)
                    processed_count['fr'] += 1
                else:
                    skipped_count['fr'] += 1
        except Exception as e:
            logging.error(f"Error processing FR data for {subcategory}: {e}")

        logging.info(f" > {subcategory}: en={len(ds_standardized[subcategory]['en'])}, fr={len(ds_standardized[subcategory]['fr'])}")

    logging.info(f"Total standardized: EN={processed_count['en']}, FR={processed_count['fr']}")
    logging.info(f"Total skipped: EN={skipped_count['en']}, FR={skipped_count['fr']}")

    pickle_file = os.path.join(script_dir, "ds_selected.pkl")
    logging.info(f"Saving standardized data to {pickle_file}...")
    try:
        with open(pickle_file, "wb") as f:
            pickle.dump(ds_standardized, f, protocol=pickle.HIGHEST_PROTOCOL)
        logging.info("Data saved successfully.")
    except Exception as e:
        logging.error(f"Failed to save data to pickle file: {e}")

if __name__ == "__main__":
    pickle_file = os.path.join(script_dir, "ds_selected.pkl")
    if os.path.exists(pickle_file):
        logging.warning(f"Pickle file '{pickle_file}' already exists.")
        user_input = input("Do you want to overwrite it? (yes/no): ").lower()
        if user_input == 'yes':
            logging.info("Overwriting existing file...")
            save_datasets()
        else:
            logging.info("Exiting without overwriting.")
    else:
        save_datasets()