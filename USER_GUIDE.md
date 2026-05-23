# Semester Toggle Feature - User Guide

## Feature Overview
The Progress Tracking chart on the dashboard now includes toggle buttons allowing users to switch between 1st and 2nd semester views.

## Location
- **Page**: Dashboard (main page after login)
- **Section**: "Progress Tracking" card in the upper left area
- **Buttons**: Located next to the "Add Grade" button

## How to Use

### 1. View 1st Semester Data (Default)
- The dashboard loads with the 1st semester view by default
- The "1st Sem" button is highlighted in the toggle group

### 2. Switch to 2nd Semester
1. Click the "2nd Sem" button in the Progress Tracking header
2. The chart will smoothly update to show 2nd semester data
3. The button will become highlighted to indicate it's active
4. Target grades are filtered to show only 2nd semester goals

### 3. Switch Back to 1st Semester
1. Click the "1st Sem" button to return to 1st semester view
2. The chart updates immediately

## What Changes When Switching Semesters

### Chart Data
- **Grading Periods**: Shows periods configured for that semester
- **Grades**: Displays grades recorded for the selected semester
- **Target Grades**: Shows only active goals assigned to that semester

### Visual Indicators
- **Button State**: Active button is highlighted
- **Chart Legend**: Updates to show relevant grading periods
- **Data Labels**: Reflects current semester's grades and targets

## Example Scenarios

### Scenario 1: Tracking Multiple Years
If a student is repeating a subject, they can:
1. Check their 1st semester performance
2. Click "2nd Sem" to see how they improved
3. Compare targets and achievements between semesters

### Scenario 2: Planning for Next Semester
- View 1st semester results to understand patterns
- Switch to 2nd semester view to see projected targets
- Identify subjects needing improvement

## Technical Details

### Button Styling
- Uses Bootstrap styling for consistency
- Responsive design works on mobile, tablet, and desktop
- Clear visual feedback for active semester

### Data Handling
- Each semester displays its configured grading periods
- Targets are automatically filtered by semester
- Missing data is gracefully handled with null values

### Browser Compatibility
Works on all modern browsers:
- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Troubleshooting

### Buttons Not Appearing
- Ensure you've recorded grades for both semesters
- Check that your browser's JavaScript is enabled

### Chart Not Updating
- Refresh the page (F5)
- Clear browser cache
- Ensure you have active goals set for the semester

### No Data in 2nd Semester
- This is normal if no grades have been recorded yet for 2nd semester
- The chart will display when you add 2nd semester grades and goals

