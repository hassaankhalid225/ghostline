@echo off
rem Launch Ghostline from a source checkout.
cd /d "%~dp0"
start "" pythonw run.pyw %*
