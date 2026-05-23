# 📊 Semester Performance Toggle - Visual Guide

## Dashboard Layout After Update

```
╔═══════════════════════════════════════════════════════════════╗
║                   STUDY TRACK DASHBOARD                       ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  Metric Cards: Overall Average | Standing | Notifications    ║
║                                                               ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │ Semester Performance 📈                                 │ ║
║  │ Midterm & Endterm Grades vs Goals                        │ ║
║  │                                                          │ ║
║  │         [1st Sem]  [2nd Sem]  ← NEW TOGGLE BUTTONS     │ ║
║  │                                                          │ ║
║  │  ┌────────────────────────────────────────────────┐    │ ║
║  │  │                                                │    │ ║
║  │  │  Multi-line Time Series Chart                  │    │ ║
║  │  │                                                │    │ ║
║  │  │  ━━━ Midterm Actual      (Blue Solid)        │    │ ║
║  │  │  ━━━ Midterm Actual      (Blue Solid)        │    │ ║
║  │  │  - - Midterm Goal        (Blue Dashed)       │    │ ║
║  │  │  ━━━ Endterm Actual      (Green Solid)       │    │ ║
║  │  │  - - Endterm Goal        (Green Dashed)      │    │ ║
║  │  │  ╱╱╱ Semester Trend      (Orange Fill)       │    │ ║
║  │  │                                                │    │ ║
║  │  │        Math    English    Science             │    │ ║
║  │  └────────────────────────────────────────────────┘    │ ║
║  │                                                          │ ║
║  │  Legend: Solid = Actual Grades | Dashed = Target Goals │ ║
║  │          Orange fill = Semester Trend                  │ ║
║  └──────────────────────────────────────────────────────────┘ ║
║                                                               ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  ┌──────────────────────────────────┐  ┌──────────────────┐ ║
║  │ Progress Tracking               │  │ Quick Actions    │ ║
║  │ [1st Sem][2nd Sem][+ Add Grade] │  │ • Record Grade   │ ║
║  │                                 │  │ • Add Goal       │ ║
║  │ [Bar Chart Display]             │  │ • Notifications  │ ║
║  └──────────────────────────────────┘  └──────────────────┘ ║
║                                                               ║
╠═══════════════════════════════════════════════════════════════╣
║  Subject Performance Tables & Recent Grades                   ║
╚═══════════════════════════════════════════════════════════════╝
```

## Toggle Button Interaction

### State 1: 1st Semester Selected (Default)
```
┌─────────────────────────────────────────────────────────┐
│ Semester Performance 📈                                  │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ [1ST SEM] [2nd Sem]  ← 1st Sem button is ACTIVE    │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                         │ │
│ ┌──────────────────────────────────────────────────────┐ │
│ │  1st Semester Chart                                 │ │
│ │  ✓ VISIBLE (display: block)                         │ │
│ │                                                     │ │
│ │  Math | English | Science                           │ │
│ │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━        │ │
│ │  (1st semester data displayed)                      │ │
│ └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### State 2: 2nd Semester Selected
```
┌─────────────────────────────────────────────────────────┐
│ Semester Performance 📈                                  │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ [1st Sem] [2ND SEM]  ← 2nd Sem button is ACTIVE    │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                         │ │
│ ┌──────────────────────────────────────────────────────┐ │
│ │  2nd Semester Chart                                 │ │
│ │  ✓ VISIBLE (display: block)                         │ │
│ │                                                     │ │
│ │  Physics | History | Biology                        │ │
│ │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━        │ │
│ │  (2nd semester data displayed)                      │ │
│ └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Button Styling

### Active Button
```
┌─────────────┐  ┌──────────────┐
│ [1ST SEM]   │  │  2nd Sem     │
└─────────────┘  └──────────────┘
 ↑ Active Style   Inactive Style
 Darker fill      Lighter/outline
 Highlighted      Normal
```

### Inactive Button
```
┌──────────────┐  ┌─────────────┐
│  1st Sem     │  │ [2ND SEM]   │
└──────────────┘  └─────────────┘
 Inactive Style    ↑ Active Style
 Lighter/outline   Darker fill
 Normal            Highlighted
```

## JavaScript Flow

### User Clicks "2nd Sem"
```
┌─────────────────────────────────────────────┐
│ User clicks [2nd Sem] button                │
└────────────────────┬────────────────────────┘
                     ↓
        ┌────────────────────────────┐
        │ JavaScript detects click   │
        └────────────────┬───────────┘
                         ↓
        ┌────────────────────────────┐
        │ Get button and container   │
        │ references                 │
        └────────────────┬───────────┘
                         ↓
        ┌────────────────────────────────────────┐
        │ 1. Add 'active' class to 2nd Sem button│
        │ 2. Remove 'active' from 1st Sem button │
        └────────────────┬───────────────────────┘
                         ↓
        ┌────────────────────────────────────────┐
        │ 1. Hide 1st Sem (display: none)        │
        │ 2. Show 2nd Sem (display: block)       │
        └────────────────┬───────────────────────┘
                         ↓
        ┌────────────────────────────────┐
        │ 2nd Semester Chart Displays    │
        │ with updated data              │
        └────────────────────────────────┘
```

## Mobile Responsive View

### Tablet View (768px - 1199px)
```
┌────────────────────────────┐
│ Semester Performance 📈     │
│ [1st Sem] [2nd Sem]        │
│                            │
│ ┌──────────────────────┐   │
│ │  Chart               │   │
│ │  (full width)        │   │
│ │                      │   │
│ └──────────────────────┘   │
│ Legend & Info              │
└────────────────────────────┘
```

### Mobile View (< 768px)
```
┌──────────────────┐
│ Sem Performance  │
│ [1st] [2nd]      │
│                  │
│ ┌────────────┐   │
│ │  Chart     │   │
│ │ (full w)   │   │
│ │            │   │
│ └────────────┘   │
│ Legend & Info    │
└──────────────────┘
```

## Implementation Details

### HTML Structure
```html
<div class="card">
  <div class="card-body">
    <!-- Header with title and buttons -->
    <div class="d-flex justify-content-between">
      <div>
        <h3>Semester Performance 📈</h3>
      </div>
      <div class="btn-group btn-group-sm">
        <button id="btn-ts-sem1" class="btn active">1st Sem</button>
        <button id="btn-ts-sem2" class="btn">2nd Sem</button>
      </div>
    </div>
    
    <!-- 1st Semester Chart (visible by default) -->
    <div id="timeSeriesSem1Container" style="display: block;">
      <canvas id="timeSeriesSem1Chart"></canvas>
    </div>
    
    <!-- 2nd Semester Chart (hidden by default) -->
    <div id="timeSeriesSem2Container" style="display: none;">
      <canvas id="timeSeriesSem2Chart"></canvas>
    </div>
    
    <!-- Legend -->
    <div class="legend">
      Legend: Solid = Actual | Dashed = Goal | Orange = Trend
    </div>
  </div>
</div>
```

### JavaScript Logic
```javascript
// Get elements
const btnTsSem1 = document.getElementById('btn-ts-sem1');
const btnTsSem2 = document.getElementById('btn-ts-sem2');
const container1 = document.getElementById('timeSeriesSem1Container');
const container2 = document.getElementById('timeSeriesSem2Container');

// 1st Sem button listener
btnTsSem1.addEventListener('click', function() {
  btnTsSem1.classList.add('active');
  btnTsSem2.classList.remove('active');
  container1.style.display = 'block';
  container2.style.display = 'none';
});

// 2nd Sem button listener
btnTsSem2.addEventListener('click', function() {
  btnTsSem2.classList.add('active');
  btnTsSem1.classList.remove('active');
  container1.style.display = 'none';
  container2.style.display = 'block';
});
```

## Benefits Comparison

| Aspect | Before | After |
|--------|--------|-------|
| **Screen Space** | Crowded (2 charts) | Spacious (1 chart) |
| **Mobile UX** | Poor (side-by-side) | Good (full-width) |
| **Navigation** | N/A | Fast toggle |
| **Focus** | Split attention | Single semester |
| **Responsiveness** | Requires scrolling | Native adaptation |

## Summary

✨ The new toggle system provides:
- 🎯 **Focused View** - See one semester at a time
- 🔀 **Quick Switch** - Toggle instantly between semesters
- 📱 **Better Mobile** - Cleaner on small screens
- 🎨 **Professional UI** - Consistent with existing buttons
- ⚡ **Fast Performance** - Instant display changes

**Status: ✅ COMPLETE AND FULLY FUNCTIONAL**

