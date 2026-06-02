$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Execute main.py using the parent directory's virtual environment
..\.venv\Scripts\python.exe main.py
