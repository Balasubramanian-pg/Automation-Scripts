First, let's get the commented code. Then we'll break it into islands and finally, the README.

      
let
    // **Source:** Connects to the specified folder path.
    Source = Folder.Files("C:\Users\ASUS\Downloads\07-03-2025YYY 2025 maker"),

    // **Removed Columns:**  Removes metadata columns about the files, keeping only essential information.
    #"Removed Columns" = Table.RemoveColumns(Source,{"Extension", "Date accessed", "Date modified", "Date created", "Attributes", "Folder Path"}),

    // **Filtered Hidden Files1:** Excludes any hidden files from the folder.
    #"Filtered Hidden Files1" = Table.SelectRows(#"Removed Columns", each [Attributes]?[Hidden]? <> true),

    // **Invoke Custom Function1:**  Applies a custom function named "Transform File" to the 'Content' of each file.
    // **Assumption:** There is a custom function named "Transform File" defined elsewhere in your Power Query.
    #"Invoke Custom Function1" = Table.AddColumn(#"Filtered Hidden Files1", "Transform File", each #"Transform File"([Content])),

    // **Removed Other Columns1:** Selects only the "Transform File" column, which now contains the transformed table from each file.
    #"Removed Other Columns1" = Table.SelectColumns(#"Invoke Custom Function1", {"Transform File"}),

    // **Expanded Table Column1:** Combines tables from all files into a single table by expanding the "Transform File" column.
    #"Expanded Table Column1" = Table.ExpandTableColumn(#"Removed Other Columns1", "Transform File", Table.ColumnNames(#"Transform File"(#"Sample File"))),

    // **Changed Type:** Sets the data type of the first 15 columns to text. This is a broad initial type assignment.
    #"Changed Type" = Table.TransformColumnTypes(#"Expanded Table Column1",{{"Column1", type text}, {"Column2", type text}, {"Column3", type text}, {"Column4", type text}, {"Column5", type text}, {"Column6", type text}, {"Column7", type text}, {"Column8", type text}, {"Column9", type text}, {"Column10", type text}, {"Column11", type text}, {"Column12", type text}, {"Column13", type text}, {"Column14", type text}, {"Column15", type text}}),

    // **Removed Columns1:** Removes the 15th column ("Column15").
    #"Removed Columns1" = Table.RemoveColumns(#"Changed Type",{"Column15"}),

    // **Added Conditional Column (IsMakerData):**  Identifies rows where "Column1" starts with "Maker Month Wise Data".
    // **Purpose:** To mark rows that contain Maker header information.
    #"Added Conditional Column" = Table.AddColumn(#"Removed Columns1", "IsMakerData", each
        if [Column1] <> null and Text.StartsWith([Column1], "Maker Month Wise Data") then
            true
        else
            false
    ),

    // **Added Maker Text:** Extracts the "Maker Month Wise Data" text from Column1 for rows marked as "IsMakerData = true".
    // **Purpose:** To capture the Maker header text.
    #"Added Maker Text" = Table.AddColumn(#"Added Conditional Column", "MakerText", each
        if [IsMakerData] then [Column1] else null
    ),

    // **Filled Down Maker:** Propagates the "MakerText" downwards to apply to all rows until the next Maker header is encountered.
    // **Purpose:** To associate each data row with its corresponding Maker header.
    #"Filled Down Maker" = Table.FillDown(#"Added Maker Text", {"MakerText"}),

    // **Updated Maker Column (NewColumn1):**  Replaces values in "Column1" under certain conditions:
    // - If "Column1" is null OR
    // - If "Column1" can be converted to a number (meaning it's likely a data row, not a header)
    // Then replace it with the "MakerText" (the extracted Maker header).
    // Otherwise, keep the original value in "Column1".
    #"Updated Maker Column" = Table.AddColumn(#"Filled Down Maker", "NewColumn1", each
        if [Column1] = null or (try Number.From([Column1]) is number otherwise false) then
            [MakerText]
        else
            [Column1]
    ),

    // **Removed Temp Columns:** Removes the temporary columns "IsMakerData" and "MakerText".
    #"Removed Temp Columns" = Table.RemoveColumns(#"Updated Maker Column", {"IsMakerData", "MakerText", "Column1"}),
    // **Renamed Columns:** Renames "NewColumn1" back to "Column1", effectively replacing the original "Column1".
    #"Renamed Columns" = Table.RenameColumns(#"Removed Temp Columns", {{"NewColumn1", "Column1"}}),
    // **Reordered Columns:**  Orders the columns.
    #"Reordered Columns" = Table.ReorderColumns(#"Renamed Columns",{"Column1", "Column2", "Column3", "Column4", "Column5", "Column6", "Column7", "Column8", "Column9", "Column10", "Column11", "Column12", "Column13", "Column14"}),

    // **Removed Top Rows:** Skips the first 3 rows of the table.
    // **Assumption:** The first 3 rows are headers or irrelevant information.
    #"Removed Top Rows" = Table.Skip(#"Reordered Columns",3),

    // **Promoted Headers:** Uses the first row of the remaining data as column headers.
    #"Promoted Headers" = Table.PromoteHeaders(#"Removed Top Rows", [PromoteAllScalars=true]),

    // **Changed Type1:** Sets data types for the newly promoted header columns to text.
    #"Changed Type1" = Table.TransformColumnTypes(#"Promoted Headers",{{"", type text}, {"_1", type text}, {"JAN", type text}, {"FEB", type text}, {"MAR", type text}, {"APR", type text}, {"MAY", type text}, {"JUN", type text}, {"JUL", type text}, {"AUG", type text}, {"SEP", type text}, {"OCT", type text}, {"NOV", type text}, {"DEC", type text}}),

    // **Renamed Columns1:** Renames the first two columns to "RTO" and "Maker". The original column names were likely empty string "" and "_1" after promoting headers.
    #"Renamed Columns1" = Table.RenameColumns(#"Changed Type1",{{"", "RTO"}, {"_1", "Maker"}}),

    // **Extracted RTO Parts:** Creates a new column "RTOParts" which is a record containing extracted RTO Name, Code, and State from the "RTO" column.
    // **Logic:**  Assumes "RTO" column starts with "Maker Month Wise Data of [RTO NAME] - [RTO CODE], [STATE]".
    #"Extracted RTO Parts" = Table.AddColumn(#"Renamed Columns1", "RTOParts", each
        if [RTO] <> null and Text.StartsWith([RTO], "Maker Month Wise Data") then
            let
                // Get the part after "of "
                AfterOf = Text.AfterDelimiter([RTO], "of "),

                // Extract RTO NAME (between "of " and " - ")
                RtoName = Text.BeforeDelimiter(AfterOf, " - "),

                // Extract RTO CODE (between " - " and ", ")
                RtoCodePart = Text.AfterDelimiter(AfterOf, " - "),
                RtoCode = Text.BeforeDelimiter(RtoCodePart, ", "),

                // Extract STATE (after ", ")
                StatePart = Text.AfterDelimiter(AfterOf, ", "),
                // Remove any year in parentheses -  Handles cases like "State Name (Year)"
                State = if Text.Contains(StatePart, "(") then
                            Text.BeforeDelimiter(StatePart, " (")
                        else
                            StatePart
            in
                [RtoName = RtoName, RtoCode = RtoCode, State = State]
        else
            [RtoName = null, RtoCode = null, State = null]
    ),

    // **Expanded RTOParts:** Expands the record column "RTOParts" into three separate columns: "RTO NAME", "RTO CODE", and "STATE".
    #"Expanded RTOParts" = Table.ExpandRecordColumn(#"Extracted RTO Parts", "RTOParts", {"RtoName", "RtoCode", "State"}, {"RTO NAME", "RTO CODE", "STATE"}),

    // **Filled Down RTO Parts:**  Propagates the RTO Name, Code, and State downwards.
    // **Purpose:** To associate each data row with its corresponding RTO information.
    #"Filled Down RTO Parts" = Table.FillDown(#"Expanded RTOParts", {"RTO NAME", "RTO CODE", "STATE"}),

    // **Removed Original RTO:** Removes the original "RTO" column as the information is now in separate columns.
    #"Removed Original RTO" = Table.RemoveColumns(#"Filled Down RTO Parts", {"RTO"}),

    // **Reordered Final Columns:**  Arranges the columns in the desired final order, placing RTO details at the beginning.
    #"Reordered Final Columns" = Table.ReorderColumns(#"Removed Original RTO",
        {"RTO NAME", "RTO CODE", "STATE", "Maker", "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"}),

    // **Filtered Rows:**  Removes rows where the "Maker" column is null, empty, or contains a specific whitespace string.
    // **Purpose:** To clean up data and remove rows without Maker information.
    #"Filtered Rows" = Table.SelectRows(#"Reordered Final Columns", each ([Maker] <> null and [Maker] <> "" and [Maker] <> "                      Maker                       "))
in
    #"Filtered Rows"

    

IGNORE_WHEN_COPYING_START
Use code with caution.Powerquery
IGNORE_WHEN_COPYING_END

Now, let's break down the code into "island" chunks and explain each.

Island 1: Source and Initial Cleanup

      
let
    // **Source:** Connects to the specified folder path.
    Source = Folder.Files("C:\Users\ASUS\Downloads\07-03-2025YYY 2025 maker"),

    // **Removed Columns:**  Removes metadata columns about the files, keeping only essential information.
    #"Removed Columns" = Table.RemoveColumns(Source,{"Extension", "Date accessed", "Date modified", "Date created", "Attributes", "Folder Path"}),

    // **Filtered Hidden Files1:** Excludes any hidden files from the folder.
    #"Filtered Hidden Files1" = Table.SelectRows(#"Removed Columns", each [Attributes]?[Hidden]? <> true),

    // **Invoke Custom Function1:**  Applies a custom function named "Transform File" to the 'Content' of each file.
    // **Assumption:** There is a custom function named "Transform File" defined elsewhere in your Power Query.
    #"Invoke Custom Function1" = Table.AddColumn(#"Filtered Hidden Files1", "Transform File", each #"Transform File"([Content]))

    

IGNORE_WHEN_COPYING_START
Use code with caution.Powerquery
IGNORE_WHEN_COPYING_END

Explanation - Island 1:

    Source = Folder.Files(...): This line is the starting point. It uses the Folder.Files function to connect to a specific folder path on your computer ("C:\Users\ASUS\Downloads\07-03-2025YYY 2025 maker"). This retrieves a table containing metadata about each file in that folder (like name, content, etc.).

    #"Removed Columns" = Table.RemoveColumns(...): This step cleans up the initial folder data. Table.RemoveColumns is used to get rid of columns that are likely not needed for further processing. It removes columns like "Extension", "Date accessed", "Date modified", etc., focusing on the core file information.

    #"Filtered Hidden Files1" = Table.SelectRows(...): This line ensures that hidden files are excluded. Table.SelectRows filters the table, keeping only rows where the "Hidden" attribute (if it exists) is not true.

    #"Invoke Custom Function1" = Table.AddColumn(...): This is a crucial step that assumes you have a custom Power Query function named "Transform File". It adds a new column named "Transform File" to the table. For each file, it calls the "Transform File" function, passing the [Content] of the file as input. The result of this function (presumably a table representing the data inside the file) is placed in the new "Transform File" column. This suggests that "Transform File" is responsible for reading the data from each file (like CSV, Excel, etc.) and converting it into a table format that Power Query can work with.

Island 2: Expanding and Initial Type Conversion

      
// **Removed Other Columns1:** Selects only the "Transform File" column, which now contains the transformed table from each file.
    #"Removed Other Columns1" = Table.SelectColumns(#"Invoke Custom Function1", {"Transform File"}),

    // **Expanded Table Column1:** Combines tables from all files into a single table by expanding the "Transform File" column.
    #"Expanded Table Column1" = Table.ExpandTableColumn(#"Removed Other Columns1", "Transform File", Table.ColumnNames(#"Transform File"(#"Sample File"))),

    // **Changed Type:** Sets the data type of the first 15 columns to text. This is a broad initial type assignment.
    #"Changed Type" = Table.TransformColumnTypes(#"Expanded Table Column1",{{"Column1", type text}, {"Column2", type text}, {"Column3", type text}, {"Column4", type text}, {"Column5", type text}, {"Column6", type text}, {"Column7", type text}, {"Column8", type text}, {"Column9", type text}, {"Column10", type text}, {"Column11", type text}, {"Column12", type text}, {"Column13", type text}, {"Column14", type text}, {"Column15", type text}}),

    // **Removed Columns1:** Removes the 15th column ("Column15").
    #"Removed Columns1" = Table.RemoveColumns(#"Changed Type",{"Column15"})

    

IGNORE_WHEN_COPYING_START
Use code with caution.Powerquery
IGNORE_WHEN_COPYING_END

Explanation - Island 2:

    #"Removed Other Columns1" = Table.SelectColumns(...): After applying the "Transform File" function, you only need the transformed tables themselves. This step selects just the "Transform File" column, discarding the original file metadata.

    #"Expanded Table Column1" = Table.ExpandTableColumn(...): This is where the data from all the files is combined into a single table. Table.ExpandTableColumn takes the column containing tables ("Transform File") and merges all those tables row by row into one big table. Table.ColumnNames(#"Transform File"(#"Sample File")) is used to get the column names from a sample transformed file to ensure the expansion works correctly. "Sample File" is likely a placeholder and Power Query is smart enough to use any file from the input to get the column names.

    #"Changed Type" = Table.TransformColumnTypes(...): At this stage, all columns are likely treated as "Any" type by Power Query. This step explicitly sets the data type for the first 15 columns (from "Column1" to "Column15") to type text. This is a common practice to ensure data is treated as text initially, especially when dealing with potentially mixed data types or when further text-based processing is needed.

    #"Removed Columns1" = Table.RemoveColumns(...): This line simply removes the 15th column ("Column15"). It's unclear from the context why column 15 is specifically removed, but it might be an unnecessary or unwanted column in the source data.

Island 3: Identifying and Extracting Maker Information

      
// **Added Conditional Column (IsMakerData):**  Identifies rows where "Column1" starts with "Maker Month Wise Data".
    // **Purpose:** To mark rows that contain Maker header information.
    #"Added Conditional Column" = Table.AddColumn(#"Removed Columns1", "IsMakerData", each
        if [Column1] <> null and Text.StartsWith([Column1], "Maker Month Wise Data") then
            true
        else
            false
    ),

    // **Added Maker Text:** Extracts the "Maker Month Wise Data" text from Column1 for rows marked as "IsMakerData = true".
    // **Purpose:** To capture the Maker header text.
    #"Added Maker Text" = Table.AddColumn(#"Added Conditional Column", "MakerText", each
        if [IsMakerData] then [Column1] else null
    ),

    // **Filled Down Maker:** Propagates the "MakerText" downwards to apply to all rows until the next Maker header is encountered.
    // **Purpose:** To associate each data row with its corresponding Maker header.
    #"Filled Down Maker" = Table.FillDown(#"Added Maker Text", {"MakerText"}),

    // **Updated Maker Column (NewColumn1):**  Replaces values in "Column1" under certain conditions:
    // - If "Column1" is null OR
    // - If "Column1" can be converted to a number (meaning it's likely a data row, not a header)
    // Then replace it with the "MakerText" (the extracted Maker header).
    // Otherwise, keep the original value in "Column1".
    #"Updated Maker Column" = Table.AddColumn(#"Filled Down Maker", "NewColumn1", each
        if [Column1] = null or (try Number.From([Column1]) is number otherwise false) then
            [MakerText]
        else
            [Column1]
    )

    

IGNORE_WHEN_COPYING_START
Use code with caution.Powerquery
IGNORE_WHEN_COPYING_END

Explanation - Island 3:

    #"Added Conditional Column" = Table.AddColumn(...): This step adds a new column called "IsMakerData". It checks if [Column1] in each row starts with the text "Maker Month Wise Data". If it does, it sets "IsMakerData" to true; otherwise, it's false. This is used to identify header rows that contain Maker information.

    #"Added Maker Text" = Table.AddColumn(...): Adds another column, "MakerText". If "IsMakerData" is true for a row, it copies the content of [Column1] into "MakerText". Otherwise, "MakerText" is set to null. This extracts the actual Maker header text when it's identified.

    #"Filled Down Maker" = Table.FillDown(...): This is a crucial step for handling header/data relationships. Table.FillDown takes the "MakerText" column and fills null values below a non-null value with that non-null value. This effectively propagates the Maker header information down to all the data rows that belong to that Maker section until the next Maker header row is encountered.

    #"Updated Maker Column" = Table.AddColumn(...): This step is a bit more complex. It aims to clean up and standardize the "Column1" to represent the Maker. It adds a new column "NewColumn1" and applies the following logic:

        Condition: If [Column1] is either null OR if [Column1] can be successfully converted to a number (using Number.From and error handling with try...otherwise), then...

        Action: Replace the value with the "MakerText" (the filled-down Maker header).

        Else: Otherwise, keep the original value of [Column1].
        This logic is designed to replace potential data rows (which might be numeric or null in "Column1") with the associated Maker header, while keeping any original text values in "Column1" that are not meant to be replaced. It's a way to restructure the data so that each row is associated with its Maker.

Island 4: Cleanup and Reordering for Maker Column

      
// **Removed Temp Columns:** Removes the temporary columns "IsMakerData" and "MakerText".
    #"Removed Temp Columns" = Table.RemoveColumns(#"Updated Maker Column", {"IsMakerData", "MakerText", "Column1"}),
    // **Renamed Columns:** Renames "NewColumn1" back to "Column1", effectively replacing the original "Column1".
    #"Renamed Columns" = Table.RenameColumns(#"Removed Temp Columns", {{"NewColumn1", "Column1"}}),
    // **Reordered Columns:**  Orders the columns.
    #"Reordered Columns" = Table.ReorderColumns(#"Renamed Columns",{"Column1", "Column2", "Column3", "Column4", "Column5", "Column6", "Column7", "Column8", "Column9", "Column10", "Column11", "Column12", "Column13", "Column14"}),

    // **Removed Top Rows:** Skips the first 3 rows of the table.
    // **Assumption:** The first 3 rows are headers or irrelevant information.
    #"Removed Top Rows" = Table.Skip(#"Reordered Columns",3)

    

IGNORE_WHEN_COPYING_START
Use code with caution.Powerquery
IGNORE_WHEN_COPYING_END

Explanation - Island 4:

    #"Removed Temp Columns" = Table.RemoveColumns(...): This step cleans up the temporary columns "IsMakerData" and "MakerText" that were used for processing the Maker information. These columns are no longer needed in the final output.

    #"Renamed Columns" = Table.RenameColumns(...): Renames the "NewColumn1" column (which now contains the processed Maker information) back to "Column1". This effectively replaces the original "Column1" with the cleaned and filled-down Maker information.

    #"Reordered Columns" = Table.ReorderColumns(...): This step reorders the columns, placing "Column1" (now the Maker column) at the beginning, followed by columns "Column2" through "Column14". This is for organizational purposes, likely to put the key identifier column first.

    #"Removed Top Rows" = Table.Skip(...): This line removes the first 3 rows from the table. It's assumed that these top rows are headers or introductory information that are not needed in the final data.

Island 5: Header Promotion and Initial Column Renaming

      
// **Promoted Headers:** Uses the first row of the remaining data as column headers.
    #"Promoted Headers" = Table.PromoteHeaders(#"Removed Top Rows", [PromoteAllScalars=true]),

    // **Changed Type1:** Sets data types for the newly promoted header columns to text.
    #"Changed Type1" = Table.TransformColumnTypes(#"Promoted Headers",{{"", type text}, {"_1", type text}, {"JAN", type text}, {"FEB", type text}, {"MAR", type text}, {"APR", type text}, {"MAY", type text}, {"JUN", type text}, {"JUL", type text}, {"AUG", type text}, {"SEP", type text}, {"OCT", type text}, {"NOV", type text}, {"DEC", type text}}),

    // **Renamed Columns1:** Renames the first two columns to "RTO" and "Maker". The original column names were likely empty string "" and "_1" after promoting headers.
    #"Renamed Columns1" = Table.RenameColumns(#"Changed Type1",{{"", "RTO"}, {"_1", "Maker"}})

    

IGNORE_WHEN_COPYING_START
Use code with caution.Powerquery
IGNORE_WHEN_COPYING_END

Explanation - Island 5:

    #"Promoted Headers" = Table.PromoteHeaders(...): This step promotes the first row of the current table to become the column headers. After removing the top 3 rows, the 4th row in the original data becomes the header row. [PromoteAllScalars=true] is an option that helps handle cases where header values might not be strings.

    #"Changed Type1" = Table.TransformColumnTypes(...): After promoting headers, the new column headers are treated as text. This step explicitly sets the data type for all these columns (including "JAN", "FEB", ..., "DEC") to type text.

    #"Renamed Columns1" = Table.RenameColumns(...): This step renames the first two columns. After header promotion, the first column likely gets a default name of "" (empty string) and the second "_1". This step renames them to "RTO" and "Maker" respectively, giving them more meaningful names.

Island 6: Extracting and Filling Down RTO Information

      
// **Extracted RTO Parts:** Creates a new column "RTOParts" which is a record containing extracted RTO Name, Code, and State from the "RTO" column.
    // **Logic:**  Assumes "RTO" column starts with "Maker Month Wise Data of [RTO NAME] - [RTO CODE], [STATE]".
    #"Extracted RTO Parts" = Table.AddColumn(#"Renamed Columns1", "RTOParts", each
        if [RTO] <> null and Text.StartsWith([RTO], "Maker Month Wise Data") then
            let
                // Get the part after "of "
                AfterOf = Text.AfterDelimiter([RTO], "of "),

                // Extract RTO NAME (between "of " and " - ")
                RtoName = Text.BeforeDelimiter(AfterOf, " - "),

                // Extract RTO CODE (between " - " and ", ")
                RtoCodePart = Text.AfterDelimiter(AfterOf, " - "),
                RtoCode = Text.BeforeDelimiter(RtoCodePart, ", "),

                // Extract STATE (after ", ")
                StatePart = Text.AfterDelimiter(AfterOf, ", "),
                // Remove any year in parentheses -  Handles cases like "State Name (Year)"
                State = if Text.Contains(StatePart, "(") then
                            Text.BeforeDelimiter(StatePart, " (")
                        else
                            StatePart
            in
                [RtoName = RtoName, RtoCode = RtoCode, State = State]
        else
            [RtoName = null, RtoCode = null, State = null]
    ),

    // **Expanded RTOParts:** Expands the record column "RTOParts" into three separate columns: "RTO NAME", "RTO CODE", and "STATE".
    #"Expanded RTOParts" = Table.ExpandRecordColumn(#"Extracted RTO Parts", "RTOParts", {"RtoName", "RtoCode", "State"}, {"RTO NAME", "RTO CODE", "STATE"}),

    // **Filled Down RTO Parts:**  Propagates the RTO Name, Code, and State downwards.
    // **Purpose:** To associate each data row with its corresponding RTO information.
    #"Filled Down RTO Parts" = Table.FillDown(#"Expanded RTOParts", {"RTO NAME", "RTO CODE", "STATE"}),

    // **Removed Original RTO:** Removes the original "RTO" column as the information is now in separate columns.
    #"Removed Original RTO" = Table.RemoveColumns(#"Filled Down RTO Parts", {"RTO"})

    

IGNORE_WHEN_COPYING_START
Use code with caution.Powerquery
IGNORE_WHEN_COPYING_END

Explanation - Island 6:

    #"Extracted RTO Parts" = Table.AddColumn(...): This step extracts RTO-related information from the "RTO" column. It assumes that when the "RTO" column starts with "Maker Month Wise Data", it contains a string in the format: "Maker Month Wise Data of [RTO NAME] - [RTO CODE], [STATE]".

        It uses Text.AfterDelimiter and Text.BeforeDelimiter functions to parse this string and extract "RTO NAME", "RTO CODE", and "STATE".

        It handles a case where the state might have a year in parentheses (e.g., "State Name (Year)") and removes the year part.

        The extracted parts are stored as a record in a new column called "RTOParts". If the "RTO" column doesn't start with "Maker Month Wise Data", "RTOParts" is set to null.

    #"Expanded RTOParts" = Table.ExpandRecordColumn(...): This expands the record column "RTOParts" into three separate columns: "RTO NAME", "RTO CODE", and "STATE". Each record in "RTOParts" is split into its individual fields, creating new columns in the main table.

    #"Filled Down RTO Parts" = Table.FillDown(...): Similar to how Maker information was filled down, this step uses Table.FillDown to propagate the "RTO NAME", "RTO CODE", and "STATE" downwards. This assumes that the RTO information acts as a header for subsequent rows, and it associates each data row with its corresponding RTO details.

    #"Removed Original RTO" = Table.RemoveColumns(...): After extracting and filling down the RTO information into separate columns, the original "RTO" column is no longer needed and is removed.

Island 7: Final Reordering and Filtering

      
// **Reordered Final Columns:**  Arranges the columns in the desired final order, placing RTO details at the beginning.
    #"Reordered Final Columns" = Table.ReorderColumns(#"Removed Original RTO",
        {"RTO NAME", "RTO CODE", "STATE", "Maker", "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"}),

    // **Filtered Rows:**  Removes rows where the "Maker" column is null, empty, or contains a specific whitespace string.
    // **Purpose:** To clean up data and remove rows without Maker information.
    #"Filtered Rows" = Table.SelectRows(#"Reordered Final Columns", each ([Maker] <> null and [Maker] <> "" and [Maker] <> "                      Maker                       "))
in
    #"Filtered Rows"

    

IGNORE_WHEN_COPYING_START
Use code with caution.Powerquery
IGNORE_WHEN_COPYING_END

Explanation - Island 7:

    #"Reordered Final Columns" = Table.ReorderColumns(...): This is the final column reordering step. It arranges the columns in the desired output order, placing "RTO NAME", "RTO CODE", and "STATE" at the beginning, followed by "Maker" and then the monthly columns "JAN" to "DEC".

    #"Filtered Rows" = Table.SelectRows(...): This is the final data cleaning step. It filters out rows based on the "Maker" column. It removes rows where the "Maker" column is:

        null (empty value)

        "" (empty text string)

        "                      Maker                       " (a specific string containing spaces and the word "Maker").
        This filtering ensures that only rows with valid Maker information are included in the final output, cleaning up any rows that might be incomplete or irrelevant.

    in #"Filtered Rows": This in keyword at the very end specifies that the final output of the entire query is the table resulting from the "Filtered Rows" step.

Finally, here's the "best in class" README file for this M Query code.

      
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
