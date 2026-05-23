# 📊 Time Series Charts - Visual Reference Guide

## Dashboard Layout

```
╔════════════════════════════════════════════════════════════════╗
║                    STUDY TRACK DASHBOARD                       ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  ║
║  │ Overall Average │  │ Academic Stand. │  │ Unread Notes │  ║
║  │      85.3       │  │      Good       │  │      3       │  ║
║  └─────────────────┘  └─────────────────┘  └──────────────┘  ║
║                                                                ║
║  ╔════════════════════════════════════════════════════════╗   ║
║  ║ 📈 1ST SEMESTER PERFORMANCE                            ║   ║
║  ║ Midterm & Endterm Grades vs Goals                      ║   ║
║  ║                                                        ║   ║
║  ║     100 ┤                                              ║   ║
║  ║         │                        ◆                     ║   ║
║  ║      85 ├─────────────●─────────────────              ║   ║
║  ║         │            ╱│        ◆                      ║   ║
║  ║      75 ├───────────●─┼───────────                    ║   ║
║  ║         │          ╱  │  ╱                            ║   ║
║  ║         └──────────────────────────────               ║   ║
║  ║         Math      English    Science                  ║   ║
║  ║                                                        ║   ║
║  ║  Legend: ━━━ Actual  - - - Goal  ◆ Trend             ║   ║
║  ╚════════════════════════════════════════════════════════╝   ║
║                                                                ║
║  ╔════════════════════════════════════════════════════════╗   ║
║  ║ 📈 2ND SEMESTER PERFORMANCE                            ║   ║
║  ║ Midterm & Endterm Grades vs Goals                      ║   ║
║  ║                                                        ║   ║
║  ║     100 ┤                                              ║   ║
║  ║         │           ◆                                 ║   ║
║  ║      90 ├─ - - - - - - - - - - - ◆ -                 ║   ║
║  ║         │          ╱          ╱   │                   ║   ║
║  ║      80 ├─────────●───────●───┤   ◆                  ║   ║
║  ║         │        ╱       ╱    │  ╱                    ║   ║
║  ║         └──────────────────────────────               ║   ║
║  ║         Math      English    Science                  ║   ║
║  ║                                                        ║   ║
║  ║  Legend: ━━━ Actual  - - - Goal  ◆ Trend             ║   ║
║  ╚════════════════════════════════════════════════════════╝   ║
║                                                                ║
║  ┌─────────────────────────────────────┐  ┌──────────────┐   ║
║  │ 📊 PROGRESS TRACKING                │  │ Quick Actions│   ║
║  │ [1st Sem] [2nd Sem] [+ Add Grade]   │  │              │   ║
║  │                                     │  │ • Record     │   ║
║  │ ▯ ▯ ▯  ▯ ▯ ▯  ▯ ▯ ▯                │  │ • Goal       │   ║
║  │ Math  English  Science              │  │ • Notif.     │   ║
║  └─────────────────────────────────────┘  └──────────────┘   ║
║                                                                ║
║  [Subject Performance Tables / Recent Grades / Notifications] ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

## Chart Components Breakdown

### Time Series Chart Structure
```
┌────────────────────────────────────────────────────┐
│ 📈 1ST SEMESTER PERFORMANCE                        │
│ Midterm & Endterm Grades vs Goals                  │
├────────────────────────────────────────────────────┤
│                                                    │
│  Y-Axis                                            │
│  (Grade 0-100)                                     │
│  │     ◆ Endterm Actual                           │
│  │    ╱ │ - Endterm Goal                          │
│  ├───●──◆────────────────────────────             │
│  │  ╱ │   Midterm Goal (- - -)                    │
│  │ ●   ◆                                           │
│  │╱                                                │
│  └──────────────────────────────────              │
│     Math    English    Science                     │
│           X-Axis                                   │
│          (Subjects)                                │
│                                                    │
│  ── Solid    = Actual Grade Recorded              │
│  - - Dashed  = Target Goal                        │
│  ╱ Slope    = Improvement Trend                   │
│  ◆ Triangle = Goal Point Marker                   │
│  ● Circle   = Actual Grade Point Marker           │
└────────────────────────────────────────────────────┘
```

## Data Series Color & Style Guide

### Midterm (Blue)
```
━━━━━━━━━━━━━━━  MIDTERM ACTUAL     Solid Line
                 (Real grade received)
                 Color: #2563eb (Blue)
                 
- - - - - - - -  MIDTERM GOAL       Dashed Line  
                 (Target you set)
                 Color: #2563eb (Blue)
                 Points: △ Triangles
```

### Endterm (Green)
```
━━━━━━━━━━━━━━━  ENDTERM ACTUAL     Solid Line
                 (Real grade received)
                 Color: #059669 (Green)
                 
- - - - - - - -  ENDTERM GOAL       Dashed Line
                 (Target you set)
                 Color: #059669 (Green)
                 Points: △ Triangles
```

### Semester Trend (Orange)
```
╱╱╱╱╱╱╱╱╱╱╱╱╱  SEMESTER TREND      Filled Area
               (Average of both periods)
               Color: #f97316 (Orange)
               Opacity: 15% fill
```

## Interactive Features

### Hover Tooltips
```
When you hover over a data point:

┌─────────────────────────┐
│ Math                    │
├─────────────────────────┤
│ Midterm Actual: 82.5    │
│ Midterm Goal: 85.0      │
│ Endterm Actual: 86.3    │
│ Endterm Goal: 85.0      │
│ Semester Trend: 84.4    │
└─────────────────────────┘
```

## Example Scenarios

### Scenario 1: Improving Student
```
Mathematics 1st Semester
100 │                        
    │                    ◆
 85 ├─────────●─────────/────
    │        /│ ◆     /
 80 ├───────/ │ ────●
    │        ◆
    └──────────────────────
    Midterm→Endterm

Status: ✓ IMPROVING - Grades going up!
```

### Scenario 2: Student Below Target
```
English 2nd Semester  
100 │ - - - ─ - - - -
    │       │
 90 ├   ◆   │   ◆
    │  / │  │  / (Goal stays at 90)
 80 ├ ●  │ ●┤
    │    │  │
    └────────────────────
    Midterm→Endterm

Status: ⚠️  BELOW TARGET - Need improvement
```

### Scenario 3: Consistently Excellent
```
Science 1st Semester
100 │                  ◆
    │◆              / /
 95 ├─────────●────◆──
    │        /│    /
 90 ├───────  ────
    │
    └──────────────────────
    Midterm→Endterm

Status: ✓ EXCELLENT - Exceeding targets!
```

### Scenario 4: Empty Semester
```
2nd Semester Performance

     (No chart displayed)
     
"Ready for data to be added"
```

## Legend Explanation

### Line Styles
```
━━━━━━━━  Solid Line     = Your actual grades (real data)
- - - - - Dashed Line    = Your target goals (what you want)
●●●●●●●  Dotted Line    = Not used in this chart
```

### Point Markers
```
● Circle             = Actual grade point
△ Triangle           = Target goal point
◆ Diamond            = Not used (for future expansion)
■ Square             = Not used (for future expansion)
```

### Data Series Identification
```
Visual     │ Name              │ What it Shows
───────────┼──────────────────┼──────────────────────
Blue ━━    │ Midterm Actual   │ Your actual midterm grade
Blue - -   │ Midterm Goal     │ Your target for midterm
Green ━━   │ Endterm Actual   │ Your actual endterm grade
Green - -  │ Endterm Goal     │ Your target for endterm
Orange ╱╱  │ Semester Trend   │ Your average performance
```

## Responsive Design

### Desktop (1200px+)
```
┌──────────────────┬──────────────────┐
│  1st Sem Chart   │  2nd Sem Chart   │
│  (col-lg-6)      │  (col-lg-6)      │
└──────────────────┴──────────────────┘
```

### Tablet (768px - 1199px)
```
┌──────────────────────────────────────┐
│         1st Sem Chart (full)         │
├──────────────────────────────────────┤
│         2nd Sem Chart (full)         │
└──────────────────────────────────────┘
```

### Mobile (< 768px)
```
┌──────────────────┐
│ 1st Sem (stacked)│
├──────────────────┤
│ 2nd Sem (stacked)│
└──────────────────┘
(may need scrolling)
```

## Quick Reference

| Element | Purpose | Visual |
|---------|---------|--------|
| Solid Blue Line | Your Midterm Score | ━━━ in Blue |
| Dashed Blue Line | Midterm Target | - - - in Blue |
| Solid Green Line | Your Endterm Score | ━━━ in Green |
| Dashed Green Line | Endterm Target | - - - in Green |
| Orange Fill | Overall Trend | ╱╱╱ in Orange |

---

**Legend Key** 🔑
- 📈 Chart shows temporal progression (time series)
- 🎯 Dashed vs Solid comparison: Goal vs Actual
- 📊 5 metrics per semester for complete view
- 🔄 Separate charts prevent data mixing
- ✨ Interactive for detailed insights

