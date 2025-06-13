# download_dataset.py
from datasets import load_dataset
import os

# 下載資料
ds = load_dataset("r13922a24/nlptestrun")

# 設定儲存資料夾
save_dir = os.path.join(os.path.dirname(__file__), "ds_saved")

# 儲存整個 DatasetDict 到磁碟
ds.save_to_disk(save_dir)

print(f"Results saved in {save_dir}")
