# StudyTrack

StudyTrack is a Django-based academic progress monitoring system for college students using the **CHED (Commission on Higher Education) grading system**. It enables students to register, set academic calendars, record grades with CHED components, set subject-specific targets, track progress with predictive analytics, and receive intelligent alerts when performance falls below expectations.

## Key Features

### 1. **Academic Calendar Selection**
- Students choose between **Semester** (2 terms/year) or **Trimester** (3 terms/year) structures during registration
- Dynamically determines grading component organization and calculation methods

### 2. **CHED Grading Components**
Supports standard CHED grading components with configurable weights:
- Attendance (10%)
- Participation (10%)
- Quizzes (20%)
- Assignments (20%)
- Midterm Exam (20%)
- Final Exam (20%)
- Project Work (Custom %)

### 3. **Intelligent Grade Tracking**
- Record grades by subject, grading period, and component
- Automatic CHED weighted average calculation per subject
- Overall academic performance tracking with letter grades

### 4. **Predictive Analytics**
- **Minimum Grade Calculator**: Determines the minimum grade required in remaining assessment terms to:
  - Achieve the student's target grade
  - Meet the passing threshold (75)
- Helps students understand what grades they need in future assessments
- Real-time calculations based on current performance

### 5. **Goal Setting & Monitoring**
- Set target grades for each subject
- Display goal achievement progress
- Compare actual performance against targets

### 6. **Intelligent Notifications**
- Alerts when grades fall below target goals
- Warnings for grades below the passing threshold (75)
- Predictive alerts when high grades are needed to meet targets
- All notifications marked as read when viewed

### 7. **Interactive Dashboard**
- Overall academic standing with performance categories
- Subject summary cards showing:
  - Latest grade
  - CHED weighted average
  - Progress toward goals
  - Minimum grade required in remaining terms
- Period-based performance chart (Prelim, Midterm, Finals, Project)
- Recent grades list
- Recent notifications preview

## User Workflow

### Registration & Setup
1. Register account with username, email, and password
2. **Select academic calendar** (Semester or Trimester) - critical for grading period calculations
3. Complete profile with institution, program, and year level

### Adding Subjects & Goals
1. Navigate to **"Add Subject and Goal"** page
2. Create new subjects/goals with target grades
3. System immediately usable even without any grades

### Recording Grades
1. Toggle to **"Add Grade"** panel on the same page
2. Select subject, grading period (Prelim/Midterm/Finals/Project), and CHED component
3. Enter score (0-100) and optional weight percentage
4. System automatically generates smart notifications

### Monitoring Progress
1. View **Dashboard** for comprehensive performance overview
2. Check **predictive grades** showing what's needed for remaining terms
3. Review **Notifications** for alerts and actionable insights
4. Update **Profile** to change academic calendar or details

## Technical Implementation

### Models
- **StudentProfile**: Stores grading structure (semester/trimester), institution, program, year level
- **Subject**: Course name linked to user
- **Goal**: Target grade per subject with active state
- **GradeEntry**: Individual grade with CHED component, weight, period
- **Notification**: Smart alerts for goal/threshold comparisons

### Calculations
- **CHED Weighted Average**: Considers component weights within grading periods
- **Predictive Grade**: Machine learning-ready calculation for remaining terms
- **Academic Standing**: 5-level categorization (Excellent to Needs Improvement)

### Forms & Fields
- Custom registration with grading structure selection
- Component-based grade entry form
- Profile management with academic calendar editing

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Browse to `http://localhost:8000/` to access the application.

## Testing

Run the comprehensive test suite:
```powershell
python manage.py test StudyTrack.tests -v 2
```

All 8 tests cover:
- User registration with grading structure selection
- Grade entry with CHED components and notifications
- Predictive calculations and goal tracking
- Dashboard and profile management
- Authentication and authorization

## CHED Grading System Notes

- **1.0 - 1.5**: Excellent (90-100)
- **1.5 - 2.0**: Very Good (85-89)
- **2.0 - 2.5**: Good (80-84)
- **2.5 - 3.0**: Fair (75-79)
- **3.0+**: Needs Improvement (<75)

The system uses 0-100 point scale internally for consistency and flexibility across institutions.

## Technology Stack
- **Backend**: Django 4.0+, Python 3.10+
- **Database**: SQLite (development) / PostgreSQL (production-ready)
- **Frontend**: Bootstrap 5.3, Chart.js
- **Authentication**: Django built-in authentication system

## Future Enhancements
- Grade prediction ML model using historical data
- Mobile app for grade logging
- Export grades to official transcripts
- Parent/Guardian notifications
- Multi-subject course grouping
- Integration with university SIS systems


