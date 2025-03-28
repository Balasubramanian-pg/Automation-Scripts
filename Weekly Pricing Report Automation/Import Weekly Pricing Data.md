Here’s the **VBA code to import weekly pricing data** from an external Excel file into your pricing sheet.  

---

### **Steps for Weekly Pricing Data Import**
1. **Open Source File** – Select the weekly pricing file.  
2. **Copy Data** – Extract pricing data from the source sheet.  
3. **Paste Data into the Pricing Sheet** – Overwrite previous data.  
4. **Close Source File** – Avoid unnecessary files being open.  

---

### **VBA Code for Importing Weekly Pricing Data**
```vba
Sub ImportPricingData()
    Dim ws As Worksheet, srcWb As Workbook, srcWs As Worksheet
    Dim lastRow As Long, srcFilePath As String
    Dim dataRange As Range, destRange As Range
    
    ' Set destination worksheet
    Set ws = ThisWorkbook.Sheets("Pricing Data")
    
    ' Define the source file path (update path accordingly)
    srcFilePath = "C:\Path\To\WeeklyPricing.xlsx" ' Change to actual file path
    
    ' Check if the file exists
    If Dir(srcFilePath) = "" Then
        MsgBox "Source file not found!", vbExclamation, "File Error"
        Exit Sub
    End If
    
    ' Open the source workbook
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    Set srcWb = Workbooks.Open(srcFilePath)
    
    ' Set source worksheet (assuming first sheet)
    Set srcWs = srcWb.Sheets(1)
    
    ' Find last row in source file
    lastRow = srcWs.Cells(srcWs.Rows.Count, "A").End(xlUp).Row
    
    ' Define data range to copy
    Set dataRange = srcWs.Range("A2:Z" & lastRow) ' Adjust columns as needed
    
    ' Define destination range
    Set destRange = ws.Range("A2")
    
    ' Clear previous data
    ws.Range("A2:Z" & ws.Cells(ws.Rows.Count, "A").End(xlUp).Row).ClearContents
    
    ' Copy & paste values only
    dataRange.Copy
    destRange.PasteSpecial Paste:=xlPasteValues
    
    ' Close source file
    srcWb.Close SaveChanges:=False
    
    ' Turn on screen updating
    Application.ScreenUpdating = True
    Application.DisplayAlerts = True
    
    ' Notify user
    MsgBox "Weekly pricing data imported successfully!", vbInformation, "Import Complete"

End Sub
```

---

### **Next Steps**
Would you like to add **pricing validation checks, calculations, or automatic report generation** after the import? 🚀
