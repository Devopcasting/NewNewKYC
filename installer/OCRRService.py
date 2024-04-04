import subprocess
import sys
import configparser


def get_powershell_executed_flag():
    config = configparser.ConfigParser()
    config.read(r'C:\Program Files (x86)\OCRR\config\configuration.ini')
    return config.getboolean('Flags', 'powershell_executed')

def set_powershell_executed_flag(value):
    config = configparser.ConfigParser()
    config.read(r'C:\Program Files (x86)\OCRR\config\configuration.ini')
    config.set('Flags', 'powershell_executed', str(value))
    with open(r'C:\Program Files (x86)\OCRR\config\configuration.ini', 'w') as config_file:
        config.write(config_file)

def run_powershell_command(command):
    try:
        # Use the subprocess module to run the PowerShell command
        subprocess.run(['powershell.exe', '-Command', command], capture_output=True, text=True, check=True)
        
        # Print the output of the PowerShell command
        print("Setting Execution Policy to RemoteSigned")
    except subprocess.CalledProcessError as e:
        # If there's an error while running the command, print the error message
        print("Error:", e)

def run_powershell_script(script_path, *args):
    try:
        # Use the subprocess module to run the PowerShell script with arguments
        command = ['powershell.exe', '-File', script_path] + list(args)
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        # Print the output of the PowerShell script
        print("Output of the PowerShell script:")
        print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        # If there's an error while running the script, print the error message
        print("Error:", e)

def write_python_path_to_ini():
    # Get the path of the currently installed Python interpreter
    python_path = sys.executable
    
    # Create a ConfigParser object
    config = configparser.ConfigParser(allow_no_value=True)
    
    # Read the existing configuration.ini file
    config.read(r'C:\Program Files (x86)\OCRR\config\configuration.ini')
    
    # Update the 'python' section with the Python path
    config.set('Paths', 'python', python_path)
    
    # Write the updated configuration to the file
    with open(r'C:\Program Files (x86)\OCRR\config\configuration.ini', 'w') as config_file:
        config.write(config_file)
    
    print("Python path updated in configuration.ini")

if __name__ == "__main__":
    # Check if powershell_executed flag is false
    if not get_powershell_executed_flag():
        # Set the execution policy to RemoteSigned
        run_powershell_command("Set-ExecutionPolicy RemoteSigned")
        # Set the powershell_executed flag to true
        set_powershell_executed_flag(True)

    # Specify the path to your PowerShell script
    script_path = r'C:\Program Files (x86)\OCRR\service\install_ocrr_engine_service.ps1'

    # Check if any arguments are provided
    if len(sys.argv) > 1:
        """Write the Python environment path if the argument is install"""
        if sys.argv[1] == "install":
            print("Writing Python environment path")
            write_python_path_to_ini()
        # Call the function to run the PowerShell script with arguments
        run_powershell_script(script_path, *sys.argv[1:])
    else:
        print("No arguments provided. Please provide one of the following options: start, stop, delete, restart, install, uninstall")
        sys.exit(1)
