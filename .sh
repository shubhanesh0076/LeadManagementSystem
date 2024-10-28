#!/bin/bash 
uvicorn LMS.asgi:application --host 127.0.0.1 --port 8000 --reload