# Dashboard Semester Toggle Feature - Implementation Summary

## Overview
Added a semester toggle button to the Progress Tracking chart on the dashboard, allowing users to switch between viewing 1st and 2nd semester data.

## Changes Made

### 1. Backend Changes (`StudyTrack/views.py`)

#### Moved variable definition
- Moved `goals_by_subject_sem` dictionary definition to before the `build_datasets_for()` function to fix Python scoping issues
- This dictionary maps (subject_id, semester) tuples to Goal objects

#### Created helper function
- Added `build_datasets_for(period_choices_for_sem, semester_key)` function that:
  - Takes period choices and semester key as parameters
  - Builds datasets for grading periods based on the provided period choices
  - Filters target goals by the specified semester
  - Returns a list of datasets compatible with Chart.js

#### Generated semester-specific datasets
- `datasets_sem1`: Built using sem1_period_choices and FIRST_SEM goals
- `datasets_sem2`: Built using sem2_period_choices and SECOND_SEM goals
- `datasets`: Default dataset (kept for backward compatibility)

#### Updated context dictionary
- Added `chart_datasets_sem1_json`: JSON string of semester 1 datasets
- Added `chart_datasets_sem2_json`: JSON string of semester 2 datasets
- Added `chart_period_labels_sem1_json`: JSON string of semester 1 period labels
- Added `chart_period_labels_sem2_json`: JSON string of semester 2 period labels

### 2. Frontend Changes (`templates/dashboard.html`)

#### Added semester toggle buttons
- Placed a button group with "1st Sem" and "2nd Sem" buttons next to the "Add Grade" button in the Progress Tracking card header
- Used Bootstrap's btn-group component for proper styling
- Buttons have IDs `btn-sem1` and `btn-sem2` for JavaScript targeting
- 1st semester button is active by default

#### JavaScript functionality
- Loaded sem1 and sem2 datasets from context into JavaScript variables
- Added `cloneDatasets()` helper function to create fresh copies of datasets (avoids Chart.js reference issues)
- Created `switchToSemester(sem)` function that:
  - Takes a semester identifier ('1' or '2')
  - Swaps the chart datasets
  - Triggers chart redraw via `gradesChart.update()`
- Wired up click event listeners to both buttons:
  - Updates button active state
  - Calls switchToSemester() with appropriate semester

## Features

✅ **Semester Toggle**: Users can click buttons to switch between 1st and 2nd semester views
✅ **Smart Targets**: Target grades are filtered by semester, showing only relevant goals
✅ **Visual Feedback**: Buttons show active state to indicate current semester
✅ **Smooth Updates**: Chart smoothly transitions between datasets
✅ **Backward Compatible**: Default dataset maintained for backward compatibility
✅ **Responsive**: Works on all screen sizes with Bootstrap styling

## Testing

All functionality has been verified:
- Dashboard loads without errors
- Context contains all required JSON variables
- Datasets are properly formatted and parseable
- HTML renders all semester buttons
- JavaScript functions are properly wired
- Chart updates correctly on button clicks

## Files Modified

1. `StudyTrack/views.py` - Dashboard view with new semester-specific dataset generation
2. `templates/dashboard.html` - Added buttons and JavaScript toggle functionality

## Browser Compatibility

Works with all modern browsers that support:
- ES6 JavaScript
- Chart.js library
- Bootstrap 5.3.3

## Notes

- The targets are now correctly filtered by semester, so users see only the goals relevant to the selected semester
- The chart maintains responsive behavior and data labels properly
- The implementation doesn't require any new dependencies

