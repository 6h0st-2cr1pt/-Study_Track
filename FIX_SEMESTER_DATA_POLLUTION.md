# Fix: 2nd Semester Chart Showing 1st Semester Data

## Problem
The 2nd semester chart was displaying 1st semester grades even when no 2nd semester goals had been created. This happened because:
1. The `build_datasets_for()` function was including ALL subjects regardless of whether they had goals in that semester
2. Since grading period codes (like 'midterm', 'endterm') are shared between semesters, grades from 1st semester would appear when viewing 2nd semester
3. The chart labels weren't being updated when switching semesters, causing a mismatch

## Solution

### Backend Changes (`StudyTrack/views.py`)

#### 1. Filter subjects by semester
Modified `build_datasets_for()` to only include subjects that have active goals in the requested semester:
```python
def build_datasets_for(period_choices_for_sem, semester_key):
    # Only include subjects that have active goals in this semester
    subjects_for_sem = [s for s in subjects if goals_by_subject_sem.get((s.id, semester_key))]
    # ... rest of function uses subjects_for_sem instead of all subjects
```

#### 2. Generate semester-specific subject labels
Added helper function to get subject names for each semester:
```python
def get_subjects_for_sem(semester_key):
    return [s.name for s in subjects if goals_by_subject_sem.get((s.id, semester_key))]

chart_subjects_sem1 = get_subjects_for_sem(Goal.FIRST_SEM)
chart_subjects_sem2 = get_subjects_for_sem(Goal.SECOND_SEM)
```

#### 3. Updated context variables
Added new context variables for semester-specific subject labels:
- `chart_subjects_sem1_json`
- `chart_subjects_sem2_json`

### Frontend Changes (`templates/dashboard.html`)

#### 1. Load semester-specific labels
Updated JavaScript to load labels for each semester:
```javascript
const labelsDefault = JSON.parse('{{ chart_subjects_json|escapejs }}');
const labelsSem1 = JSON.parse('{{ chart_subjects_sem1_json|escapejs }}');
const labelsSem2 = JSON.parse('{{ chart_subjects_sem2_json|escapejs }}');
```

#### 2. Update chart with semester labels
Modified chart initialization and switching function to update both datasets AND labels:
```javascript
// During switch
gradesChart.data.labels = newLabels;
gradesChart.data.datasets = cloneDatasets(newDs);
gradesChart.update();
```

## Results

✅ **1st Semester Chart**: Shows only subjects with 1st semester goals and their grades
✅ **2nd Semester Chart**: Empty when no 2nd semester goals exist
✅ **No Data Pollution**: 1st semester data no longer appears in 2nd semester view
✅ **Correct Goals**: Target grades only show for relevant semesters
✅ **Proper Labels**: Chart x-axis labels update when switching semesters

## Test Verification

Created comprehensive tests that verify:
1. When only 1st semester goal exists: 2nd semester chart is completely empty
2. When both semesters have different subjects: Each semester shows only its own subjects
3. Chart labels match the displayed data

All tests pass successfully ✓

