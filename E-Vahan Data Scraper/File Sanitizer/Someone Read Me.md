Below is a simple, step-by-step README that explains what each section and function of the code does. You can use it to help someone who doesn’t know how to read code understand what the script is doing.

---

# Mass Excel Rename Script README

This script automatically renames Excel files in a specified folder. It reads the first cell (A1) from each Excel file to get a title, extracts a specific part (usually a location code), and renames the file with that code. It also logs its work and can run many files at once using multiple threads.

---

## Overview

- **Purpose:**  
  Rename Excel files based on a part of the title found in the first cell.

- **How It Works:**  
  1. Walks through a folder and all its subfolders.
  2. Reads the first cell (A1) of each Excel file.
  3. Extracts a location code from a specific title pattern.
  4. Renames the file using the extracted name.
  5. Logs details and shows a summary of the work done.

---

## Detailed Explanation by Section

### 1. Imports and Setup

- **Imports:**  
  The script uses libraries for file handling (`os`), time measurement (`time`), logging, handling warnings, working with dates (`datetime`), running tasks in parallel (`ThreadPoolExecutor`), and reading Excel files (`openpyxl`).

- **Warning Suppression:**  
  It hides some style warnings from the Excel reading library to keep the output clean.

- **Logging Configuration:**  
  A log file named `mass_excel_rename.log` is created. This file records what the script does, any errors that occur, and general progress.

- **Settings:**  
  - `ROOT_DIR`: The folder where the Excel files are located. **(Change this to your folder path!)**
  - `DEBUG_MODE`: When set to `True`, the script prints extra details and asks for confirmation before processing all files.

---

### 2. Function: `fast_read_title(file_path)`

- **What It Does:**  
  Opens an Excel file and quickly reads the first cell (A1) to get a title.
  
- **Simple Explanation:**  
  - Opens the file without loading the whole file into memory.
  - Reads the value from the top cell.
  - Converts it to text (or returns an empty string if nothing is there).
  - Closes the file and logs any errors.

---

### 3. Function: `extract_name_from_title(title, filename)`

- **What It Does:**  
  Looks at the title text and extracts the location code. For example, if the title is  
  `"Maker Month Wise Data of Baratang - AN201 , Andaman & Nicobar Island (2024)"`  
  it will extract `"Baratang - AN201"`.

- **Simple Explanation:**  
  - Checks if the title contains a specific phrase.
  - Finds the part after that phrase up to a comma or a parenthesis.
  - If it can’t find the right part, it falls back to using the original file name.

---

### 4. Function: `process_file(args)`

- **What It Does:**  
  Processes one Excel file from start to finish.

- **Simple Explanation:**  
  - Reads the title from the Excel file.
  - Extracts the location code from the title.
  - Cleans the extracted name (removes invalid characters).
  - Checks if the file really needs to be renamed.  
    - If not, it skips the file.
  - If a file with the new name already exists, it adds a timestamp to make the name unique.
  - Renames the file and logs the result (success, skipped, or error).

---

### 5. Function: `process_folder(max_workers=4)`

- **What It Does:**  
  Goes through all the folders and files, processing many files at once using threads (parallel processing).

- **Simple Explanation:**  
  - Walks through the given root directory to find all Excel files.
  - Uses a thread pool to handle multiple files simultaneously.
  - In DEBUG mode, processes a few files first and asks if you want to continue.
  - Updates you on progress by printing the number of files processed.
  - Keeps statistics on how many files were successfully renamed, skipped, or had errors.

---

### 6. Function: `print_stats(folder_stats)`

- **What It Does:**  
  Prints a table that summarizes the work done.

- **Simple Explanation:**  
  - Displays each folder with the number of files processed.
  - Shows the totals for success, errors, and skipped files.

---

### 7. Function: `analyze_sample_files()`

- **What It Does:**  
  Runs a test on a few Excel files to show what the title looks like and what name will be extracted.

- **Simple Explanation:**  
  - Looks at up to two files per folder.
  - Reads and prints the title and the extracted name.
  - This helps you verify that the extraction process is working correctly before running on all files.

---

### 8. Main Section (When You Run the Script)

- **What It Does:**  
  Checks everything before starting and then runs the file processing.

- **Simple Explanation:**  
  - Confirms the folder exists.
  - If in DEBUG mode, asks if you want to run the sample analysis.
  - Processes all files in the folder.
  - Prints the summary statistics and the total time taken.
  - Informs you where to find the log file for more details.

---

## How to Use the Script

1. **Install Python:**  
   Make sure you have Python installed on your computer.

2. **Install Required Packages:**  
   You need the `openpyxl` package. Install it using:
   ```bash
   pip install openpyxl
   ```

3. **Modify the Path:**  
   Change the `ROOT_DIR` variable in the code to point to the folder where your Excel files are stored.

4. **Set Debug Mode:**  
   You can set `DEBUG_MODE` to `False` if you do not want extra output or confirmation prompts.

5. **Run the Script:**  
   Open your command line or terminal and run:
   ```bash
   python your_script_name.py
   ```

6. **Follow On-Screen Prompts:**  
   In debug mode, you will be asked if you want to run a sample analysis before processing all files.

7. **Check the Logs:**  
   The script writes details and any errors to `mass_excel_rename.log`.

---

## Summary

This script is designed to save time by automatically renaming many Excel files based on a title inside each file. It works through your chosen folder, reads a key piece of data from each file, and renames the file accordingly. Detailed logs and progress updates help you track what’s happening. The script uses parallel processing to handle multiple files at once, making the process faster.

Feel free to ask if you have any questions or need further explanations!
