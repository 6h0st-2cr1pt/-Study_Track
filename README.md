# StudyTrack

StudyTrack is a Django-based academic progress monitoring system for college students. It lets students register, log in, record grades, set subject-specific targets, review progress trends, and receive reminders when performance falls below target.

## Features
- Student registration and authentication
- Manual grade entry by subject and grading period
- Dashboard with overall average and academic standing
- Progress chart for grading-period averages
- Goal-setting per subject
- In-app notifications for low grades and missed targets

## Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

## Notes
- Grades are entered manually by students.
- Chart rendering uses Chart.js from a CDN.
- The project uses SQLite by default for development.

