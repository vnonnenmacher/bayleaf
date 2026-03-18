#!/usr/bin/env bash
set -euo pipefail

python3 manage.py create_dosage_units
python3 manage.py load_medications
python3 manage.py seed_data --doctors 100 --patients 200 --attach-medications --slot-window-days 200
python3 manage.py seed_organizations
