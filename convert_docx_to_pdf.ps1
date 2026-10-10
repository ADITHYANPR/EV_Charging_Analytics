$docxPath = Join-Path (Get-Location) "EV_Charging_Analytics_Case_Study_Draft.docx"
$pdfPath = Join-Path (Get-Location) "EV_Charging_Analytics_Case_Study_Draft.pdf"

Write-Host "Opening Word application..."
$word = New-Object -ComObject Word.Application
$word.Visible = $false

try {
    Write-Host "Opening document: $docxPath"
    $doc = $word.Documents.Open($docxPath)
    Write-Host "Exporting to PDF: $pdfPath"
    # wdExportFormatPDF = 17
    $doc.ExportAsFixedFormat($pdfPath, 17)
    $doc.Close([ref]0)
    Write-Host "PDF successfully generated!"
}
catch {
    Write-Error "Failed to export PDF: $_"
}
finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
