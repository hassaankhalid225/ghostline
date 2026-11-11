@echo off
rem Launch Caption Assist from a source checkout.
cd /d "%~dp0"
start "" pythonw run.pyw %*
