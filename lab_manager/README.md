# VG Lab Manager

A local web-based lab management system for the VGCC Biotech Teaching Lab.

Tracks inventory, samples, DNA extractions, QC measurements (Qubit/Nanodrop),
PCR runs, Sanger sequencing runs, and qPCR runs.

---

## Requirements

- **Python 3.9 or newer** — Download from https://www.python.org/downloads/
  - On Windows: check **"Add Python to PATH"** during installation
- An internet connection for the first run (to download dependencies)

---

## Quick Start

### Mac or Linux
1. Open Terminal
2. Navigate to this folder: `cd /path/to/lab_manager`
3. Make the script executable (first time only): `chmod +x run.sh`
4. Run: `./run.sh`
5. Your browser should open automatically to http://localhost:5000

### Windows
1. Double-click `run.bat`
2. Your browser will open to http://localhost:5000

### Default Login
| Username | Password  |
|----------|-----------|
| `admin`  | `labadmin` |

**Change the password immediately after your first login** via Users → Edit.

---

## First-Time Setup: Import Your Inventory

After the app is running, open a second terminal and run:

```bash
cd /path/to/lab_manager
source venv/bin/activate   # Mac/Linux
# OR on Windows: venv\Scripts\activate.bat

python import_inventory.py
```

This will import all 185+ chemicals, supplies, and all primers/probes from
your `Chemical Inventory.xlsx` and the primer appendix into the database.

---

## Adding Users

1. Log in as `admin`
2. Click **Users** in the sidebar
3. Click **Add User**
4. Set their role:
   - **Instructor** — full access including delete and user management
   - **Staff** — same as instructor
   - **Student** — can add and view records, but cannot delete

---

## Your Data

All data is stored in a single file: `lab_manager/lab_manager.db`

**To back up your data:** Copy `lab_manager.db` to a safe location (USB drive,
Google Drive, etc.). Do this regularly.

**To restore:** Replace `lab_manager.db` with your backup copy.

---

## Daily Use Guide

| Task | Where to go |
|------|-------------|
| Check expiring items | Dashboard |
| Add a new chemical/reagent | Inventory → Add Item |
| Accession a new sample | Samples → Accession New Sample |
| Record Qubit/Nanodrop reading | QC Measurements → Record Measurement |
| Log an extraction batch | DNA Extractions → New Batch |
| Log a PCR run | PCR Runs → Log New Run |
| Log a sequencing run + upload FASTA | Sanger Sequencing → Log New Run |
| Log a qPCR run | qPCR Runs → Log New Run |

---

## Stopping the Server

Press **Ctrl+C** in the terminal window where the server is running.
Your data is saved automatically — no need to do anything special.

---

## Troubleshooting

**"Port 5000 already in use"** — Another copy is already running. Close it first,
or edit `app.py` and change `port=5000` to a different number like `port=5001`.

**Browser shows "Connection refused"** — The server isn't running. Run the
launch script again.

**Lost the admin password** — Delete `lab_manager.db` and re-run the app. This
resets everything, so export any important data first.
