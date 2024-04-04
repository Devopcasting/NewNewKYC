# Define the path to the Windows service executable
$serviceExePath = "C:\Program Files (x86)\OCRR\service\OCRR_Engine.exe"

# Define the name of the Windows service
$serviceName = "OCRR_Engine"

# Function to start the service
function Start-MyService {
    param (
        [string]$serviceName
    )
    Write-Host "Starting the service '$serviceName'..."
    Start-Service $serviceName
}

# Function to stop the service
function Stop-MyService {
    param (
        [string]$serviceName
    )
    Write-Host "Stopping the service '$serviceName'..."
    Stop-Service $serviceName
}

# Function to delete the service
function Remove-MyService {
    param (
        [string]$serviceName
    )
    Write-Host "Uninstalling the service '$serviceName'..."
    sc.exe delete $serviceName
    Write-Host "Service '$serviceName' uninstalled successfully."
}

# Function to restart the service
function Restart-MyService {
    param (
        [string]$serviceName
    )
    Stop-MyService $serviceName
    Start-MyService $serviceName
}

# Function to check the status of the service
function Get-MyServiceStatus {
    param (
        [string]$serviceName
    )
    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    if ($service) {
        Write-Host "Service '$serviceName' status: $($service.Status)"
    } else {
        Write-Host "Service '$serviceName' not found."
    }
}

# Function to install the service
function Install-MyService {
    param (
        [string]$serviceName,
        [string]$serviceExePath
    )
    # Check if the service already exists
    if (Get-Service -Name $serviceName -ErrorAction SilentlyContinue) {
        Write-Host "The service '$serviceName' already exists."
        Write-Host "Stopping '$serviceName'"
        Stop-MyService $serviceName
        Write-Host "Deleting '$serviceName'"
        Remove-MyService $serviceName
    }

    # Install the new service
    Write-Host "Installing the service '$serviceName'..."
    sc.exe create $serviceName binPath= "`"$serviceExePath`"" start=auto

    # Start the service
    Start-MyService $serviceName

    # Verify if the service has been installed and started successfully
    if (Get-Service -Name $serviceName) {
        Write-Host "Service '$serviceName' installed and started successfully."
    } else {
        Write-Host "Failed to install and start the service '$serviceName'. Please check the logs for more details."
    }
}

# Function to uninstall the service
function Uninstall-MyService {
    param (
        [string]$serviceName
    )
    Write-Host "Uninstalling the service '$serviceName'..."
    Stop-MyService $serviceName
    Remove-MyService $serviceName
}

# Check for arguments passed to the script
if ($args.Count -eq 0) {
    Write-Host "No arguments provided. Please provide one of the following options: start, stop, delete, restart, install."
    return
}

# Determine the action based on the provided argument
$action = $args[0]

switch ($action) {

    "start" {
        Start-MyService $serviceName
    }
    "stop" {
        Stop-MyService $serviceName
    }
    "delete" {
        Remove-MyService $serviceName
    }
    "restart" {
        Restart-MyService $serviceName
    }
    "status" {
        Get-MyServiceStatus $serviceName
    }
    "install" {
        Install-MyService $serviceName $serviceExePath
    }
    "uninstall" {
        Uninstall-MyService $serviceName
    }
    default {
        Write-Host "Invalid argument '$action'. Please provide one of the following options: start, stop, delete, restart."
    }
}
