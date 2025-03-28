```
Sub ExtractData()
    Dim conn As Object
    Dim rs As Object
    Dim sqlQuery As String
    Dim ws As Worksheet
    Dim connectionString As String
    
    ' Set connection string for your database
    connectionString = "Provider=SQLOLEDB;Data Source=YourServerName;Initial Catalog=YourDatabaseName;Integrated Security=SSPI;"
    
    ' SQL Query to fetch data
    sqlQuery = "SELECT * FROM PriceList WHERE EffectiveDate >= GETDATE()"
    
    ' Connect to the database
    Set conn = CreateObject("ADODB.Connection")
    conn.Open connectionString
    
    ' Execute query
    Set rs = conn.Execute(sqlQuery)
    
    ' Reference worksheet to populate
    Set ws = ThisWorkbook.Sheets("PriceData")
    
    ' Populate data
    Dim i As Long
    i = 1
    Do While Not rs.EOF
        ws.Cells(i, 1).Value = rs.Fields("Column1").Value
        ws.Cells(i, 2).Value = rs.Fields("Column2").Value
        ' Repeat for other columns
        rs.MoveNext
        i = i + 1
    Loop
    
    ' Clean up
    rs.Close
    conn.Close

    Set rs = Nothing
    Set conn = Nothing
```
    
    MsgBox "Data extracted successfully!", vbInformation
End Sub
