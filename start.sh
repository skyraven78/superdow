#!/bin/bash
gunicorn --bind 0.0.0.0:8443 importos.py

