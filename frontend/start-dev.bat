@echo off
cd /d "%~dp0"

if not exist node_modules (
  echo Installing frontend dependencies...
  npm.cmd install --cache .\.npm-cache
)

echo Starting Smart Class frontend...
echo Browser will open automatically. Keep this window open.
npm.cmd run dev:open
