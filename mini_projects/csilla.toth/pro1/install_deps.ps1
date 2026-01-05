<#
PowerShell script to create a virtual environment and install project dependencies.
Run from the `pro1` directory in PowerShell:
    .\install_deps.ps1
#>

param(
    [string]$venvName = "venv"
)

try {
    # Ensure script is not blocked by Windows
    Unblock-File -Path $MyInvocation.MyCommand.Definition -ErrorAction SilentlyContinue

    # Ensure execution policy allows running scripts for current user
    try {
        $policy = Get-ExecutionPolicy -Scope CurrentUser -ErrorAction Stop
    } catch {
        $policy = Get-ExecutionPolicy -ErrorAction SilentlyContinue
    }
    if ($policy -in @('Restricted','Undefined')) {
        Write-Host "Setting execution policy to RemoteSigned for CurrentUser..."
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force -ErrorAction SilentlyContinue
    }

    Write-Host "Creating virtual environment '$venvName'..."
    python -m venv $venvName

    Write-Host "Activating virtual environment..."
    if (Test-Path "$venvName/Scripts/Activate.ps1") {
        . "$venvName/Scripts/Activate.ps1"
    } else {
        Write-Error "Activation script not found. Ensure Python venv support is available."
        exit 1
    }

    Write-Host "Upgrading pip..."
    python -m pip install --upgrade pip

    Write-Host "Installing dependencies from requirements.txt (no pip cache)..."
    try {
        python -m pip install --no-cache-dir -r requirements.txt
    } catch {
        Write-Warning "pip install failed, attempting to purge pip cache and retry. Error: $($_.Exception.Message)"
        try {
            python -m pip cache purge 2>$null
        } catch {
            Write-Warning "Could not purge pip cache (ignored)."
        }
        try {
            python -m pip install --no-cache-dir -r requirements.txt
        } catch {
            Write-Warning "Retry failed, attempting fallback (user install). Error: $($_.Exception.Message)"
            try {
                python -m pip install --no-cache-dir --user -r requirements.txt
                Write-Host "Installed to user site-packages."
            } catch {
                Write-Error "Failed to install dependencies: $($_.Exception.Message)"
                exit 2
            }
        }
    }

    Write-Host "Done. To activate the virtualenv later run:`\n    .\\$venvName\\Scripts\\Activate.ps1"
} catch {
    Write-Error "Unexpected error: $($_.Exception.Message)"
    exit 3
}
