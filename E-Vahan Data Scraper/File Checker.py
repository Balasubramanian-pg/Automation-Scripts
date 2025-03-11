import os
import pandas as pd

folder_path = r"F:\Flipcarbon\2025\3. March\11-03-2025\2025"

for root, dirs, files in os.walk(folder_path):
    for file in files:
        file_path = os.path.join(root, file)
        try:
            if file.endswith(".xlsx"):
                pd.read_excel(file_path)  # Try reading Excel files
            elif file.endswith(".csv"):
                pd.read_csv(file_path)  # Try reading CSV files
        except Exception as e:
            print(f"File {file_path} cannot be read: {e}")
