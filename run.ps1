Set-Location -Path $PSScriptRoot

if (-Not (Test-Path "venv")) {
    python -m venv venv
    Write-Output "Virtual environment created."

    .\venv\Scripts\Activate.ps1
    Write-Output "Virtual environment activated."

    pip install -r requirements.txt
    Write-Output "Dependencies installed."
}
else {
    .\venv\Scripts\Activate.ps1
    Write-Output "Virtual environment activated."
}

python main.py
deactivate