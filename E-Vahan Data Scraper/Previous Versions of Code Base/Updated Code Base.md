import os
import pandas as pd
import re
from datetime import datetime
import glob
from openpyxl.styles import PatternFill, Border, Side, Alignment, Font

def extract_metadata(title_text, file_path):
    """
    Extract RTO name, code and state from the title text
    
    Parameters:
    title_text (str): The title text containing RTO information
    file_path (str): Path to the Excel file, used for fallback extraction
    
    Returns:
    tuple: (rto_name, rto_code, state_name)
    """
    # Regular expression to match the pattern: "of RTO_NAME - CODE , STATE_NAME (YEAR)"
    # Make the pattern more flexible for variations in spacing and format
    pattern = r"of\s+(.+?)\s+-\s+([A-Z0-9]+)\s*[,\s]+\s*(.+?)\s*\(\d{4}\)"
    match = re.search(pattern, title_text)
    
    if match:
        rto_name = match.group(1).strip()
        rto_code = match.group(2).strip()
        state_name = match.group(3).strip()
        return rto_name, rto_code, state_name
    else:
        # Fall back to another pattern if the first one doesn't match
        # Extract from filename for files like "BARPETA - AS15.xlsx"
        filename_pattern = r"([A-Za-z\s]+)\s*-\s*([A-Z0-9]+)"
        match = re.search(filename_pattern, os.path.basename(file_path))
        if match:
            rto_name = match.group(1).strip()
            rto_code = match.group(2).strip()
            # Try to extract state from path
            state_name = os.path.basename(os.path.dirname(file_path))
            return rto_name, rto_code, state_name
        
        return None, None, None

def process_excel_file(file_path):
    """
    Process a single Excel file and extract relevant data
    """
    try:
        # First, try to read the Excel file with default settings
        df = pd.read_excel(file_path, header=None)
        
        # Look for title text in first few rows
        title_text = None
        for i in range(min(5, len(df))):
            if pd.notna(df.iloc[i, 0]) and "Maker Month Wise Data" in str(df.iloc[i, 0]):
                title_text = str(df.iloc[i, 0])
                break
        
        if title_text is None:
            title_text = f"Maker Month Wise Data of {os.path.basename(file_path).split('.')[0]}"
        
        # Extract metadata with correct number of arguments
        rto_name, rto_code, state_name = extract_metadata(title_text, file_path)
        if not rto_name:
            rto_name = os.path.basename(file_path).split('.')[0]
        if not rto_code:
            rto_code = "N/A"
        if not state_name:
            state_name = os.path.basename(os.path.dirname(file_path))
        
        # Look for month columns more flexibly
        month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 
                       'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
                     
        # Find the row with month names by searching more broadly
        header_row_idx = None
        month_cols = []
        month_indices = []
        
        for i in range(len(df)):
            month_found = False
            for j in range(len(df.columns)):
                cell_value = str(df.iloc[i, j]).upper() if pd.notna(df.iloc[i, j]) else ""
                if any(month in cell_value for month in month_names):
                    month_found = True
                    break
            
            if month_found:
                header_row_idx = i
                break
        
        if header_row_idx is None:
            print(f"Could not find header row with months in {file_path}")
            return None
            
        # Find month columns in the header row
        for j in range(len(df.columns)):
            cell_value = str(df.iloc[header_row_idx, j]).upper() if pd.notna(df.iloc[header_row_idx, j]) else ""
            for month in month_names:
                if month == cell_value or cell_value.endswith(f" {month}"):
                    month_cols.append(month)
                    month_indices.append(j)
                    break
        
        if not month_cols:
            # If months not found directly, check if they're in a combined cell
            for j in range(len(df.columns)):
                cell_value = str(df.iloc[header_row_idx, j]).upper() if pd.notna(df.iloc[header_row_idx, j]) else ""
                found_months = []
                for month in month_names:
                    if month in cell_value:
                        found_months.append(month)
                
                if len(found_months) > 0:
                    # If multiple months in one cell, assume they're in consecutive columns
                    for idx, month in enumerate(found_months):
                        month_cols.append(month)
                        month_indices.append(j + idx)
        
        if not month_cols:
            print(f"Could not find month columns in {file_path}")
            return None
        
        # Find vehicle class column - typically the second column after S No
        Maker_col = None
        for j in range(len(df.columns)):
            if pd.notna(df.iloc[header_row_idx, j]) and "MAKER" in str(df.iloc[header_row_idx, j]).upper():
                Maker_col = j
                break
        
        if Maker_col is None:
            # If not found, assume it's column 1 (second column)
            Maker_col = 1
        
        # Read data rows (skip header and start from next row)
        data_start_idx = header_row_idx + 1
        data_rows = []
        
        for i in range(data_start_idx, len(df)):
            row = df.iloc[i]
            
            # Skip empty rows or rows without vehicle class
            if pd.isna(row[Maker_col]) or str(row[Maker_col]).strip() == "":
                continue
            
            Maker = str(row[Maker_col]).strip()
            
            # Skip rows that don't look like data rows
            if Maker.isdigit() or Maker.upper() == "TOTAL":
                continue
            
            # Extract monthly data
            month_data = {}
            for month, col_idx in zip(month_cols, month_indices):
                if col_idx < len(row):
                    value = row[col_idx]
                    if pd.isna(value):
                        value = 0
                    else:
                        # Convert to numeric type
                        try:
                            value = pd.to_numeric(value)
                        except:
                            # If conversion fails, try to clean the value
                            if isinstance(value, str):
                                # Remove non-numeric characters except decimal point
                                clean_value = re.sub(r'[^\d.]', '', value)
                                try:
                                    value = float(clean_value) if clean_value else 0
                                except:
                                    value = 0
                            else:
                                value = 0
                    month_data[month] = value
                else:
                    month_data[month] = 0
            
            # Create a row with all information
            data_row = {
                'RTO Name': rto_name,
                'RTO Code': rto_code,
                'State': state_name,
                'Maker': Maker,
                **month_data
            }
            data_rows.append(data_row)
        
        return data_rows
        
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None

def main():
    # Get all Excel files in the folder and subfolders
    folder_path = r"C:\Users\ASUS\Downloads\28-02-2025YYY" # Change this to your folder path
    excel_files = glob.glob(os.path.join(folder_path, "**", "*.xlsx"), recursive=True)
    
    if not excel_files:
        print("No Excel files found in the specified folder and subfolders")
        return
    
    # Process each file and collect data
    all_data = []
    for file_path in excel_files:
        print(f"Processing {file_path}...")
        file_data = process_excel_file(file_path)
        if file_data:
            all_data.extend(file_data)
    
    if not all_data:
        print("No data was extracted from the files")
        return
    
    # Create a DataFrame from all data
    result_df = pd.DataFrame(all_data)
    
    # Ensure all month columns are numeric
    month_names = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 
                  'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    
    for month in month_names:
        if month in result_df.columns:
            result_df[month] = pd.to_numeric(result_df[month], errors='coerce').fillna(0)
    
    # Generate output filename with today's date
    today = datetime.now().strftime("%d-%m-%Y")
    output_filename = f"Consolidated Maker Wise Data ({today}).xlsx"
    
    # Save to Excel with styling to avoid the warning
    with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
        result_df.to_excel(writer, index=False, sheet_name='Consolidated Data')
        
        # Apply styling to the worksheet
        workbook = writer.book
        worksheet = writer.sheets['Consolidated Data']
        
        # Define styles
        header_font = Font(bold=True, size=12)
        header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        header_fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Format header row
        for cell in worksheet[1]:
            cell.font = header_font
            cell.alignment = header_alignment
            cell.fill = header_fill
            cell.border = thin_border
        
        # Format data columns (apply borders and number format for month columns)
        for row_idx, row in enumerate(worksheet.iter_rows(min_row=2), start=2):
            for col_idx, cell in enumerate(row, start=1):
                cell.border = thin_border
                
                # Set number format for month columns
                col_letter = worksheet.cell(row=1, column=col_idx).value
                if col_letter in month_names:
                    cell.number_format = '#,##0'
        
        # Auto-adjust column widths
        for col in worksheet.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                if cell.value:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
            adjusted_width = (max_length + 2) * 1.2
            worksheet.column_dimensions[column].width = min(adjusted_width, 30)
    
    print(f"Data has been saved to {output_filename}")

if __name__ == "__main__":
    main()
    
