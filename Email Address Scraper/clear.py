import pandas as pd
import re
import os

# File paths
input_file = r"F:\Flipcarbon\2025\4. April\10-04-2025\Automotive Directors.xlsx"
output_folder = r"F:\Flipcarbon\2025\4. April\10-04-2025"
output_file = os.path.join(output_folder, "Cleaned leads.xlsx")

def clean_data(df):
    # Initialize lists to store cleaned data
    companies = []
    names = []
    designations = []
    urls = []
    
    current_company = None
    
    # Process each row in the DataFrame
    for index, row in df.iterrows():
        # Get company name from first column
        company = row[0]
        
        # If company name is valid, update current company
        if pd.notna(company) and isinstance(company, str) and company.strip():
            current_company = company.strip()
            
        # Process LinkedIn URLs and full names
        # We'll process columns in pairs: URL followed by profile info
        for i in range(1, len(row)-1, 2):
            url = row[i]
            profile_info = row[i+1]
            
            # Skip if URL or profile_info is not valid
            if not pd.notna(url) or not pd.notna(profile_info) or not isinstance(profile_info, str):
                continue
                
            # Clean profile info - typically in format "Name - Designation... LinkedIn · Name Followers"
            profile_info = profile_info.strip('"')  # Remove quotes if present
            
            # Extract the main part (before LinkedIn)
            main_parts = profile_info.split("LinkedIn")
            info = main_parts[0].strip()
            
            # Split by first hyphen to get name and designation
            if " - " in info:
                parts = info.split(" - ", 1)
                name = parts[0].strip()
                
                # Get designation (everything between first " - " and next " - " or end)
                if len(parts) > 1:
                    designation_part = parts[1]
                    # Clean the designation
                    designation = designation_part.split(" - ")[0].strip()
                    designation = re.sub(r'\.{3,}$', '', designation)  # Remove trailing dots
                else:
                    designation = ""
            else:
                # If no hyphen, take the whole thing as name
                name = info.strip()
                designation = ""
            
            # Add to our lists if we have a company and name
            if current_company and name:
                companies.append(current_company)
                names.append(name)
                designations.append(designation)
                urls.append(url)
    
    # Create new DataFrame
    result_df = pd.DataFrame({
        'Company Name': companies,
        'Person Name': names,
        'Designation': designations,
        'URL': urls
    })
    
    return result_df

try:
    # Read the Excel file
    print(f"Reading file: {input_file}")
    df = pd.read_excel(input_file)
    
    # Clean and restructure the data
    print("Processing data...")
    cleaned_df = clean_data(df)
    
    # Save the result
    print(f"Saving results to: {output_file}")
    cleaned_df.to_excel(output_file, index=False)
    
    print(f"Process completed successfully! {len(cleaned_df)} records processed.")
    print(f"Output file: {output_file}")
    
except Exception as e:
    print(f"An error occurred: {str(e)}")
