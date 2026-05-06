# StudyTrack

StudyTrack is a Django-based academic progress monitoring system for college students using the **CHED (Commission on Higher Education) grading system**. It enables students to register, set academic calendars, record grades with CHED components, set subject-specific targets, track progress with predictive analytics, and receive intelligent alerts when performance falls below expectations.

## Key Features

### 1. **Academic Calendar Selection with Dynamic Period Configuration**
- Students choose between **Semester** (2 terms/year) or **Trimester** (3 terms/year) structures during registration
- **Dynamically determines grading periods** in the Add Grade form:
  - **Semester Students**: See only **Midterm** and **Endterm** periods
  - **Trimester Students**: See **Prelim**, **Midterm**, and **Endterm** periods
- Adapts period calculations for predictive analytics based on academic calendar
- Dashboard charts dynamically show only relevant grading periods

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
- **Dynamic Period Chart**: Shows only grading periods relevant to user's academic calendar:
  - Semester students: Chart shows Midterm and Endterm performance
  - Trimester students: Chart shows Prelim, Midterm, and Endterm performance
- Subject summary cards showing:
  - Latest grade
  - CHED weighted average
  - Progress toward goals
  - Minimum grade required in remaining terms (based on remaining periods)
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
2. Select subject, **grading period** (automatically filtered based on your academic calendar!):
   - **Semester**: Midterm, Endterm
   - **Trimester**: Prelim, Midterm, Endterm
3. Select CHED component (Attendance, Quiz, Assignment, etc.)
4. Enter score (0-100) and optional weight percentage
5. System automatically generates smart notifications

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
  - Automatically accounts for student's academic calendar (2 terms for semester, 3 for trimester)
  - Calculates minimum grade needed based on completed vs remaining periods
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

## Grading Periods by Academic Calendar

### Semester System (2 Terms per Year)
- **Midterm**: Grades recorded at the middle of the semester
- **Endterm**: Final grades at the end of the semester
- **Grade Form**: Only shows Midterm and Endterm options
- **Dashboard Chart**: Displays 2-period performance trend
- **Predictive Calculations**: Computes based on 2 total periods

### Trimester System (3 Terms per Year)
- **Prelim**: Grades recorded in the first assessment period
- **Midterm**: Grades recorded in the middle period
- **Endterm**: Final grades at the end of the term
- **Grade Form**: Shows all three period options (Prelim, Midterm, Endterm)
- **Dashboard Chart**: Displays 3-period performance trend
- **Predictive Calculations**: Computes based on 3 total periods

**Example Predictive Calculation:**
- Semester student with 88 average in Midterm, target of 90
  - Needs average of **92** in Endterm to reach 90 overall
- Trimester student with two assessments completed (averages: 85 Prelim, 88 Midterm), target of 90
  - Needs average of **93** in Endterm to reach 90 overall



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


