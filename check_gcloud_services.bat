@echo off
echo Checking Google Cloud App Engine Services for Duplicates...
echo =======================================================

echo.
echo 1. Listing all App Engine services:
gcloud app services list

echo.
echo 2. Listing all App Engine versions:
gcloud app versions list

echo.
echo 3. Checking for running instances:
gcloud app instances list

echo.
echo 4. Checking current project:
gcloud config get-value project

echo.
echo 5. Checking for any VMs running accident monitors:
gcloud compute instances list --filter="name~accident"

echo.
echo 6. Checking for any scheduled jobs:
gcloud scheduler jobs list

echo.
echo === Analysis Complete ===
echo.
echo If you see multiple services or versions running the same monitoring script,
echo you likely have duplicates causing repetitive alerts.
echo.
echo Common issues:
echo - Multiple versions of 'default' service
echo - Both 'primary' and 'secondary' services running
echo - Old versions not properly deleted
echo.
pause