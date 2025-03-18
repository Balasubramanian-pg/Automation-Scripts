import pandas as pd
import os
import re
from pathlib import Path

def parse_title(title):
    """Extract RTO Code, Name, and State from the title string"""
    pattern = r'Maker Month Wise Data\s+of\s+(.+?)\s+-\s+(.+?)\s*,\s*(.+?)\s*\(\d{4}\)'
    match = re.search(pattern, title)
    if match:
        return {
            'RTO Name': match.group(1).strip(),
            'RTO Code': match.group(2).strip(),
            'State': match.group(3).strip()
        }
    raise ValueError(f"Title format not recognized: {title}")

def process_excel_file(file_path):
    """Process individual Excel file and return formatted DataFrame"""
    try:
        # Skip hidden temporary files
        if os.path.basename(file_path).startswith('~$'):
            return pd.DataFrame()

        # Read Excel without headers
        df = pd.read_excel(file_path, header=None, engine='openpyxl')
        
        # Extract title and RTO info
        title = df.iloc[0, 0]
        rto_info = parse_title(title)
        
        # Find months row
        months_row = None
        for idx, row in df.iterrows():
            if idx < 2:
                continue  # Skip title and header rows
            if pd.notna(row[2]) and re.match(r'^(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)$', 
                                           str(row[2]).strip().upper()):
                months_row = idx
                break
        
        if not months_row:
            print(f"Skipping {file_path}: Month row not found")
            return pd.DataFrame()
        
        # Extract headers
        months = df.iloc[months_row, 2:-1].values  # Exclude TOTAL column
        months = [str(m).strip().upper() for m in months if pd.notna(m)]
        
        # Extract data
        data_start = months_row + 1
        headers = ['Maker'] + months + ['TOTAL']
        data = df.iloc[data_start:, [1] + list(range(2, 2+len(months))) + [df.shape[1]-1]]
        data.columns = headers
        
        # Clean data
        data = data.dropna(subset=['Maker']).reset_index(drop=True)
        data['Maker'] = data['Maker'].str.strip()
        
        # Add RTO information with correct column names
        for col in ['RTO Code', 'RTO Name', 'State']:
            data[col] = rto_info[col]
        
        # Reorder columns
        final_columns = ['RTO Code', 'RTO Name', 'State', 'Maker'] + months + ['TOTAL']
        return data[final_columns]
    
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return pd.DataFrame()

def main(input_folder, output_file):
    """Main function to process all Excel files"""
    all_data = pd.DataFrame()
    
    # Process all Excel files in input folder and subfolders
    for root, _, files in os.walk(input_folder):
        for file in files:
            if file.lower().endswith(('.xlsx', '.xls')):
                file_path = os.path.join(root, file)
                print(f"Processing: {file_path}")
                df = process_excel_file(file_path)
                if not df.empty:
                    all_data = pd.concat([all_data, df], ignore_index=True)
    
    # Handle numeric columns
    month_cols = [col for col in all_data.columns if col.upper() in [
        'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 
        'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']]
    
    for col in month_cols + ['TOTAL']:
        all_data[col] = pd.to_numeric(all_data[col], errors='coerce').fillna(0).astype(int)
    
    # Save consolidated data
    all_data.to_excel(output_file, index=False, engine='openpyxl')
    print(f"Consolidation complete. Saved to: {output_file}")

if __name__ == "__main__":
    input_path = Path(r"C:\Users\ASUS\Downloads\OneDrive_2025-03-18\Maker (2024)")
    output_path = Path(r"C:\Users\ASUS\Downloads\Andhra.xlsx")
    main(input_path, output_path)
