# Define the path to the Windows service executable
$serviceExePath = "C:\Program Files (x86)\OCRR\service\OCRR_Engine.exe"

# Define the name of the Windows service
$serviceName = "OCRR_Engine"

# Check if the service already exists
if (Get-Service -Name $serviceName -ErrorAction SilentlyContinue) {
    Write-Host "The service '$serviceName' already exists."
    Write-Host "Uninstalling the existing service..."
    sc.exe delete $serviceName
    Write-Host "Existing service '$serviceName' uninstalled successfully."
}

# Install the new service
Write-Host "Installing the service '$serviceName'..."

# Install the service using sc.exe
sc.exe create $serviceName binPath= "`"$serviceExePath`"" start=auto

# Start the service
Write-Host "Starting the service '$serviceName'..."
Start-Service $serviceName

# Verify if the service has been installed and started successfully
if (Get-Service -Name $serviceName) {
    Write-Host "Service '$serviceName' installed and started successfully."
} else {
    Write-Host "Failed to install and start the service '$serviceName'. Please check the logs for more details."
}