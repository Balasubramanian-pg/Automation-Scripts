# Power Query Transformation for Maker Month Wise Data

## Description

This Power Query (M Query) code is designed to process data files from a specified folder, transforming them into a structured table suitable for analysis. The code is specifically tailored for files containing "Maker Month Wise Data," likely related to regional transport office (RTO) data, organized by maker and month.

The transformation performs the following key actions:

1. **Connects to a folder:** Reads files from a given folder path.
2. **Extracts data:**  Assumes each file contains tabular data and uses a custom function `Transform File` to extract this data into a table format.
3. **Combines data:** Merges data from all files into a single table.
4. **Identifies and propagates headers:** Recognizes rows starting with "Maker Month Wise Data" as headers for Maker and RTO information and propagates this header information down to subsequent data rows.
5. **Extracts RTO details:** Parses RTO name, code, and state from the RTO header rows.
6. **Restructures data:** Creates separate columns for RTO Name, RTO Code, State, Maker, and monthly data (JAN-DEC).
7. **Cleans data:** Removes unnecessary columns, top rows, and rows with missing or invalid Maker information.
8. **Standardizes output:** Ensures consistent column naming and data types.

## Code Explanation (Islands)

The M Query code is broken down into logical islands, each performing a specific set of operations:

**Island 1: Source and Initial Cleanup**
- Connects to the specified folder.
- Removes file metadata columns.
- Filters out hidden files.
- Invokes the custom `Transform File` function to process each file's content.

**Island 2: Expanding and Initial Type Conversion**
- Selects the transformed table column.
- Expands tables from all files into one.
- Sets initial data type for the first 15 columns to text.
- Removes the 15th column.

**Island 3: Identifying and Extracting Maker Information**
- Identifies rows with "Maker Month Wise Data" as Maker headers.
- Extracts the Maker header text.
- Fills down the Maker header text to apply it to data rows.
- Updates "Column1" to represent the Maker based on header information.

**Island 4: Cleanup and Reordering for Maker Column**
- Removes temporary processing columns.
- Renames the updated Maker column to "Column1".
- Reorders columns.
- Removes top rows (assumed to be irrelevant headers).

**Island 5: Header Promotion and Initial Column Renaming**
- Promotes the first data row to be column headers.
- Sets data types for the new header columns to text.
- Renames the first two columns to "RTO" and "Maker".

**Island 6: Extracting and Filling Down RTO Information**
- Extracts RTO Name, Code, and State from the "RTO" column based on a specific format.
- Expands the extracted RTO parts into separate columns.
- Fills down RTO information to apply it to data rows.
- Removes the original "RTO" column.

**Island 7: Final Reordering and Filtering**
- Reorders columns to the final desired layout.
- Filters out rows with null, empty, or invalid Maker values.

## Usage

To use this Power Query code in Power BI or Power Query Editor:

1. **Open Power BI Desktop or Power Query Editor in Excel.**
2. **Get Data:** Choose the "Folder" connector.
3. **Folder Path:** Enter the folder path `"C:\Users\ASUS\Downloads\07-03-2025YYY 2025 maker"` (or change it to your actual folder path).
4. **Transform Data:** Click "Transform Data" to open the Power Query Editor.
5. **Advanced Editor:** In the Power Query Editor, go to "Home" -> "Advanced Editor".
6. **Paste Code:** Replace the existing code with the M Query code provided above.
7. **Custom Function:** **Important:** Ensure you have a custom function named `Transform File` defined in your query (or accessible). This function should take the file content as input and return a table. This function is not provided in this README and needs to be defined separately based on the format of your input files (e.g., CSV, Excel).
8. **Click "Done".**
9. **Review and Adjust:** Review the applied steps and the resulting table. You may need to adjust data types further or modify the code based on your specific file structure and requirements.
10. **Close & Apply:** Click "Close & Apply" to load the transformed data into Power BI or Excel.

## Assumptions

- **File Format:** The code assumes that the files in the folder are of a format that can be processed by the `Transform File` custom function (e.g., CSV, Excel).
- **Custom Function "Transform File":**  A custom function named `Transform File` is expected to exist and correctly process the file content into a table.
- **Data Structure:** Input files are expected to have a structure where "Maker Month Wise Data" and RTO information act as headers, followed by data rows.
- **RTO Format:** The "RTO" column is expected to follow the format: "Maker Month Wise Data of [RTO NAME] - [RTO CODE], [STATE]".
- **Top Rows:** The first 3 rows of data after file transformation are assumed to be irrelevant and are skipped.
- **Column Order:** The code is designed for a specific column order and may need adjustments if the input file structure varies significantly.

## Parameters

- **Folder Path:** `"C:\Users\ASUS\Downloads\07-03-2025YYY 2025 maker"` - This is hardcoded in the `Source` step. You should modify this to point to your actual data folder.

## Output

The transformed output is a table with the following columns:

- **RTO NAME:** Extracted RTO Name.
- **RTO CODE:** Extracted RTO Code.
- **STATE:** Extracted State.
- **Maker:** Maker name, filled down from header rows.
- **JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC:** Monthly data columns (data type is initially text and may need further type conversion depending on your needs).

---

This README provides a comprehensive explanation of the M Query code. Remember to define your `Transform File` function appropriately for your file types to ensure the code works correctly. Let me know if you have any other questions!
