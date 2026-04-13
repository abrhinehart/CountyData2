@echo off
title CountyData2
start "API" cmd /k "cd /d %~dp0 && uvicorn api:app --reload --host 0.0.0.0 --port 1460"
start "UI"  cmd /k "cd /d %~dp0\ui && npm run dev"
