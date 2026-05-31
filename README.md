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

### 2. **Simple Grade Entry**
- Students record only their **final midterm or endterm grades** (no component breakdown)
- Teachers calculate CHED components (Attendance, Quizzes, Assignments, etc.) and provide the overall grade
- Clean, straightforward interface focusing on period grades only
- Optional notes field for additional context

### 3. **Simple Grade Tracking**
- Record grades by subject and grading period (Midterm or Endterm for semester; Prelim, Midterm, or Endterm for trimester)
- Automatic average calculation per subject across all grading periods
- Overall academic performance tracking with letter grades
- Teachers handle CHED component weighting before providing grades to students

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
2. Select subject and **grading period** (automatically filtered based on your academic calendar):
   - **Semester**: Midterm, Endterm
   - **Trimester**: Prelim, Midterm, Endterm
3. Enter your overall grade (0-100) for that period
4. Add optional notes if needed
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
- **GradeEntry**: Individual period grade (Prelim, Midterm, or Endterm)
- **Notification**: Smart alerts for goal/threshold comparisons

### Calculations
- **Grade Average**: Simple average of all grades in each period
- **Subject Average**: Average across all grading periods
- **Predictive Grade**: Minimum grade needed in remaining terms (accounts for semester vs trimester)
  - Automatically uses 2 periods for semester, 3 for trimester
- **Academic Standing**: 5-level categorization (Excellent to Needs Improvement)
- **Teacher Role**: Calculates CHED component weights and provides overall period grade to students

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

All 9 tests cover:
- User registration with grading structure selection
- Grade entry with CHED components and notifications
- Predictive calculations and goal tracking
- Dashboard and profile management
- Authentication and authorization

### BSIS Curriculum Seeding

To populate a user with the BSIS subject set for 1st to 4th year and both semesters, plus sample random midterm and endterm grades and active target goals, run:

```powershell
python manage.py seed_bsis_curriculum --username Fedorov
```

If the `Fedorov` account does not exist yet, the command will create it with an unusable password and then seed the curriculum subjects, grades, and goals. Re-running the command is safe and will not create duplicate subjects, grades, or goals.

## How It Works: Student vs Teacher Role

### Student Role
- **Register** and select academic calendar (Semester or Trimester)
- **Add Subjects & Goals** with target grades
- **Record Period Grades** (Midterm, Endterm, or Prelim/Midterm/Endterm)
  - Just enter the overall grade teachers give you for that period
  - No need to break down components
- **Monitor Progress** via dashboard and predictions
- **Receive Alerts** when grades fall below goals

### Teacher Role
- **Calculate CHED Components**: Grade attendance, quizzes, assignments, exams (20% each typically)
- **Combine Components**: Apply weights to calculate overall period grade (e.g., 85)
- **Provide to Students**: Students enter the 85 as their Midterm grade
- **Track in System**: Automatically aggregated for trending and predictions

This separation makes the process simple for students while maintaining academic rigor through teacher evaluation.

---

## Grading Periods by Academic Calendar

### Semester System (2 Terms per Year)
- **Midterm**: Grade recorded at the middle of the semester (calculated by teacher from components)
- **Endterm**: Final grade at the end of the semester (calculated by teacher from components)
- **Predictive Calculation**: Needs reach target based on 2 total periods

### Trimester System (3 Terms per Year)
- **Prelim**: Grade recorded in the first assessment period (calculated by teacher)
- **Midterm**: Grade recorded in the middle period (calculated by teacher)
- **Endterm**: Final grade at the end of the term (calculated by teacher)
- **Predictive Calculation**: Needs reach target based on 3 total periods

**Example:**
- Semester student has Midterm grade of 88, target 90
- To reach 90: Needs **92** average in Endterm
- Trimester student has Prelim (85) and Midterm (88), target 90
- To reach 90: Needs **93** average in Endterm



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


