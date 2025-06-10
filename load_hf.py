from datasets import load_dataset

ds = load_dataset("r13922a24/nlptestrun")

# Check the values
print(ds['train']['is_correct'][:10])  # Will show True, False, and None

# Count each type
import pandas as pd
df = pd.DataFrame(ds['train'])
print(df['is_correct'].value_counts(dropna=False))
# Output will be like:
# True     50000
# False    40000  
# NaN      10000  (these are your nulls)