# Bug Fix Summary: 2nd Semester Chart Data Pollution

## Issue Reported
**User Report:** "Why is there data in the 2nd sem chart? It should be empty because I haven't put any data yet. The data in the first sem is appearing in the 2nd sem but with no goals."

## Root Cause
The `build_datasets_for()` function was showing grades for ALL subjects, regardless of whether they had goals in that specific semester. Since grading periods are shared between semesters, this caused 1st semester grades to appear when viewing 2nd semester data.

## Changes Made

### 📝 File: `StudyTrack/views.py`

#### Change 1: Filter subjects by semester
```python
# BEFORE: All subjects shown
for s in subjects:
    g = s.grades.filter(grading_period=code)...

# AFTER: Only subjects with goals in that semester
subjects_for_sem = [s for s in subjects if goals_by_subject_sem.get((s.id, semester_key))]
for s in subjects_for_sem:
    g = s.grades.filter(grading_period=code)...
```

#### Change 2: Generate semester-specific labels
```python
def get_subjects_for_sem(semester_key):
    return [s.name for s in subjects if goals_by_subject_sem.get((s.id, semester_key))]

chart_subjects_sem1 = get_subjects_for_sem(Goal.FIRST_SEM)
chart_subjects_sem2 = get_subjects_for_sem(Goal.SECOND_SEM)
```

#### Change 3: Add context variables
```python
'chart_subjects_sem1_json': json.dumps(chart_subjects_sem1),
'chart_subjects_sem2_json': json.dumps(chart_subjects_sem2),
```

### 🎨 File: `templates/dashboard.html`

#### Change 1: Load semester-specific labels
```javascript
const labelsDefault = JSON.parse('{{ chart_subjects_json|escapejs }}');
const labelsSem1 = JSON.parse('{{ chart_subjects_sem1_json|escapejs }}');
const labelsSem2 = JSON.parse('{{ chart_subjects_sem2_json|escapejs }}');
```

#### Change 2: Update labels when switching semesters
```javascript
function switchToSemester(sem) {
    // ... determine newLabels based on semester ...
    gradesChart.data.labels = newLabels;  // NEW: Update labels
    gradesChart.data.datasets = cloneDatasets(newDs);
    gradesChart.update();
}
```

## Results

| Scenario | Before Fix | After Fix |
|----------|-----------|-----------|
| **Only 1st sem goal** | 2nd sem shows 1st sem data | ✅ 2nd sem is empty |
| **1st sem has Math, 2nd sem has English** | Both show all subjects | ✅ Each shows only its subjects |
| **Chart labels** | Mismatch with data | ✅ Labels match data |
| **Target goals** | Shows all goals mixed | ✅ Shows only relevant goals |

## Testing

✅ Test 1: 2nd semester chart is empty when no 2nd semester goals exist
✅ Test 2: Each semester shows only subjects with goals in that semester
✅ Test 3: Chart labels correctly update when switching semesters
✅ Test 4: Target grades are filtered by semester

All tests pass!

## Impact
- Users can now trust the chart to show only relevant data for the selected semester
- No more confusion from seeing data with no associated goals
- Clean separation of semester data

