Set-Location -Path $PSScriptRoot

while ($true) {
    if (-Not (Test-Path "venv")) {
        python -m venv venv
        Write-Output "Virtual environment created."

        .\venv\Scripts\Activate.ps1
        Write-Output "Virtual environment activated."

        python.exe -m pip install --upgrade pip
        Write-Output "Pip upgraded."

        pip install -r requirements.txt
        Write-Output "Dependencies installed."
    }
    else {
        .\venv\Scripts\Activate.ps1
        Write-Output "Virtual environment activated."
    }

    try {
        python main.py
    }
    finally {
        Write-Output "Cleaning up processes..."

        # Find and stop ChromeDriver processes
        $chromeDriverProcesses = Get-Process | Where-Object { $_.ProcessName -eq "chrome" }
        foreach ($process in $chromeDriverProcesses) {
            Stop-Process -Id $process.Id -Force
        }

        # Deactivate the virtual environment
        deactivate
    }

    Write-Output "Waiting for 30 minutes before next run..."
    Start-Sleep -Seconds 1800
}
