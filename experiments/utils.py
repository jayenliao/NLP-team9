import pickle
import os

def load_prepared_dataset():
    """
    Loads the prepared dataset from a pickle file.

    Args:
        file_path (str): The path to the pickle file.

    Returns:
        dict: A dictionary containing the selected datasets,
              or None if the file does not exist.
    """
    file_path = os.path.join(os.path.dirname(__file__), "..", "data", "ds_selected.pkl")
    if not os.path.exists(file_path):
        print(f"No dataset at {file_path}")
        return None
    with open(file_path, "rb") as f:
        return pickle.load(f)
    
if __name__ == "__main__":
    dataset = load_prepared_dataset()
# Test Block (remove later)
    if dataset:
        print(f"Loaded dataset contains {len(dataset)} subtasks.")
        first_subtask = list(dataset.keys())[0]
        print(f"First subtask: {first_subtask}")
        first_question_en = dataset[first_subtask]['en'][0]
        print("Example English question:", first_question_en)