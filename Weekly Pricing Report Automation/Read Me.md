# Automated Weekly Pricing Report with VBA
---

## 📝 Use Case

The project has 3 phases, connecting excel workbook directly to a data source of your choice (ERP in my case), Extracting and cleaning a routine set of information from a designated master
and then creating a neat formatted report and mailing the same to the essential stakeholders.

## 🚀 Solution

A VBA-powered workflow was implemented to automate the entire process, which:

1. Pulled data from **DataSelect** queries for account and pricing information.
2. Created customized Excel workbooks from a predefined template.
3. Sent reports via email to authorized recipients based on strict access controls.
4. Minimized manual effort, reducing the task from hours to under 5 minutes.

### Process Flow

1. **Data Extraction**:
   - Connected to the DataSelect system.
   - Fetched account and pricing data via queries.

2. **Workbook Creation**:
   - Generated a new workbook using a pre-configured Excel template.
   - Populated the workbook with account-specific data and price details.

3. **Report Distribution**:
   - Group reports sent to central teams (Finance, Credit Control).
   - Customized individual reports created and emailed to account managers.

4. **Notification**:
   - Confirmed completion of the task.

### Code Snippet

```vba
Sub GeneratePricingReports()
    ' Connect to DataSelect
    ConnectToDataSelect
    
    ' Create a new workbook from the template
    Set wb = Workbooks.Add(TemplatePath)
    wb.Name = "PricingReport_" & Format(Date, "YYYYMMDD")
    
    ' Loop through price lists
    For Each PriceList In PriceLists
        Call GeneratePriceList(wb, PriceList)
    Next PriceList
    
    ' Save the workbook
    wb.SaveAs FilePath & wb.Name
    DisconnectFromDataSelect
    
    ' Distribute Reports
    Call DistributeReports(wb)
    
    MsgBox "Pricing reports generated and sent successfully!", vbInformation
End Sub
```

### Key Features

Automation: Reduced manual work and errors.
Customization: Ensured tailored reports for each recipient.
Scalability: Adaptable for future enhancements.

💡 Thought Process

The solution was designed with these objectives:

Efficiency: Replace repetitive manual tasks with automated workflows.
Compliance: Restrict data access per legal requirements.
Usability: Simplify processes for non-technical users.

Challenges included dynamic validation, handling scope creep, and adapting to evolving business needs. This project emphasized the importance of iterative development and stakeholder collaboration.
🛠️ Advanced Formatting in Excel

The generated reports featured:

Dynamic Pivot Tables: For better data summarization.
Advanced Visuals: Donut charts, KPI cards, slicers for filtering.
Data Validation: Ensured accuracy and consistency in outputs.

🤝 Contribution

Feel free to contribute by raising issues or suggesting enhancements. Collaboration is always welcome!

📂 Repository Contents

Code/: Contains VBA scripts.
Templates/: Includes the Excel templates used for reports.
Documentation/: Detailed process documentation.

📬 Feedback

Your thoughts and feedback are invaluable. Reach out with suggestions or ideas to improve this project!
