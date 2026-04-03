# 🧠 SYNAPSE - Verification Checklist

Complete this checklist to verify the API and Dashboard are working correctly.

## ✅ Pre-Flight Checks

- [ ] Python 3.8+ installed (`python --version`)
- [ ] Node.js 16+ installed (`node --version`)
- [ ] SQLite database exists (`organizer.db` in `d:\AUTOMATION\`)
- [ ] Dependencies installed:
  - [ ] FastAPI: `pip install fastapi`
  - [ ] Uvicorn: `pip install uvicorn`
  - [ ] Node packages: `cd dashboard && npm install`

## ✅ API Server Verification

### 1. Start API Server

```bash
cd d:\AUTOMATION
python -m uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 2. Check Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "🧠 Synapse API",
  "timestamp": "2026-03-05T10:30:00"
}
```

- [ ] Health endpoint returns 200 OK
- [ ] Timestamp is current

### 3. Check API Documentation

- [ ] Navigate to `http://localhost:8000/docs`
- [ ] Swagger UI loads without errors
- [ ] All endpoints are listed

### 4. Test Key Endpoints

#### Stats Endpoint
```bash
curl http://localhost:8000/stats
```

Expected response includes:
```json
{
  "total_files": <integer>,
  "today_files": <integer>,
  "status": "operational"
}
```

- [ ] Returns status code 200
- [ ] Contains valid numeric values
- [ ] Status is "operational"

#### Categories Endpoint
```bash
curl http://localhost:8000/categories
```

Expected response:
```json
{
  "categories": [
    {"category": "COLLEGE", "count": 450},
    {"category": "PROGRAMMING", "count": 380}
  ],
  "total": 830
}
```

- [ ] Returns status code 200
- [ ] Categories list is not empty or empty (depending on data)
- [ ] Total count matches sum of categories

#### Confidence Endpoint
```bash
curl http://localhost:8000/confidence
```

Expected response includes confidence buckets:
```json
{
  "distribution": [
    {"bucket": "high", "count": 1200},
    {"bucket": "medium", "count": 180},
    {"bucket": "low", "count": 40}
  ]
}
```

- [ ] Returns status code 200
- [ ] Contains distribution array
- [ ] Has high/medium/low buckets

#### Activity Endpoint
```bash
curl http://localhost:8000/activity?limit=10
```

Expected response:
```json
{
  "activity": [
    {
      "timestamp": "2026-03-05T10:30:00",
      "file_name": "document.pdf",
      "category": "COLLEGE",
      "action": "moved",
      "confidence": 0.92
    }
  ],
  "count": 10
}
```

- [ ] Returns status code 200
- [ ] Activity is a list (can be empty)
- [ ] Count is accurate

#### Summary Endpoint
```bash
curl http://localhost:8000/summary
```

Expected response includes:
```json
{
  "overview": {
    "total_files": 1420,
    "today_files": 128,
    "files_moved": 1200,
    "files_skipped": 220
  },
  "categories": [...],
  "confidence": [...]
}
```

- [ ] Returns status code 200
- [ ] Overview section present
- [ ] Categories and confidence data included

### 5. Check CORS Headers

```bash
curl -H "Origin: http://localhost:3000" http://localhost:8000/stats -v
```

Expected headers in response:
```
access-control-allow-origin: http://localhost:3000
access-control-allow-credentials: true
access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS
```

- [ ] CORS headers are present
- [ ] Allow-Origin includes localhost:3000

## ✅ Dashboard Verification

### 1. Install Dependencies

```bash
cd d:\AUTOMATION\dashboard
npm install
```

Expected output: No errors, packages installed

- [ ] All packages installed successfully
- [ ] No critical warnings
- [ ] `node_modules` folder created

### 2. Start Dashboard

```bash
npm run dev
```

Expected output:
```
> next dev
Ready in 1.2s
```

- [ ] Server starts without errors
- [ ] Ready message appears in under 5 seconds
- [ ] Listening on port 3000

### 3. Check Dashboard Home Page

Navigate to: `http://localhost:3000`

Expected to see:
- [ ] Page loads without errors
- [ ] Title shows "🧠 SYNAPSE Dashboard"
- [ ] Subtitle shows "AI Workspace Intelligence"
- [ ] Sidebar visible on left with navigation items
- [ ] Stat cards showing: Total Files, Organized Today, System Status, Last Activity
- [ ] Recent Activity table with columns

#### Check Stats Load

- [ ] Total Files card shows a number
- [ ] Organized Today card shows a number
- [ ] System Status shows "Operational"
- [ ] Last Activity shows a timestamp or "Never"

#### Check Recent Activity Table

- [ ] Table headers visible: File name, Category, Action, Timestamp
- [ ] Rows show actual file data (or table is empty if no data)
- [ ] Category badges are colored
- [ ] Action badges show correct colors (green for moved, orange for skipped)

### 4. Check Activity Page

Navigate to: `http://localhost:3000/activity`

Expected to see:
- [ ] Page title changes to "Recent Activity"
- [ ] Table loads with full data
- [ ] Columns include: File Name, Category, Subject, Confidence, Action, Timestamp
- [ ] Confidence shows percentage with progress bar
- [ ] Action badges colored appropriately

#### Verify Activity Table

- [ ] Table can display 100+ rows
- [ ] Confidence progress bars show up
- [ ] Timestamps are formatted correctly
- [ ] Summary section at bottom shows counts

### 5. Check Analytics Page

Navigate to: `http://localhost:3000/analytics`

Expected to see:
- [ ] Page title shows "Analytics"
- [ ] Two charts load without errors
- [ ] Category Distribution chart shows data
- [ ] Confidence Distribution pie chart shows data

#### Verify Category Distribution Chart

- [ ] Bar chart displays
- [ ] X-axis shows category names
- [ ] Y-axis shows counts
- [ ] Mouse over shows tooltip
- [ ] Colors are visible

#### Verify Confidence Distribution Chart

- [ ] Pie chart displays
- [ ] Shows high/medium/low/unknown segments
- [ ] Colors differ from bar chart
- [ ] Mouse over shows labels and counts

#### Verify Statistics Table

- [ ] Table displays all categories
- [ ] Counts match chart data
- [ ] Total row highlighted
- [ ] Total count is correct

### 6. Check Settings Page

Navigate to: `http://localhost:3000/settings`

Expected to see:
- [ ] Page title shows "Settings"
- [ ] Confidence Thresholds section visible
- [ ] Three sliders for high/medium/low thresholds
- [ ] Operation Modes section with checkboxes
- [ ] Save Settings button

#### Verify Thresholds

- [ ] High threshold slider works (0-100)
- [ ] Medium threshold slider works
- [ ] Low threshold slider works
- [ ] Values update when dragged
- [ ] Percentages display correctly

#### Verify Operation Modes

- [ ] Automatic Mode checkbox present
- [ ] Preview Mode checkbox present
- [ ] Real-time Monitoring checkbox present
- [ ] Checkboxes toggle on/off

#### Verify Save Button

- [ ] Save Settings button is clickable
- [ ] Button shows feedback (hover effect)
- [ ] Click shows "Settings saved" confirmation message

## ✅ Integration Tests

### 1. End-to-End Data Flow

- [ ] API returns data
- [ ] Dashboard fetches from API
- [ ] Data displays on home page
- [ ] Data updates when page is refreshed
- [ ] No console errors in browser (F12)

### 2. Cross-Origin Requests

- [ ] Dashboard at localhost:3000 can fetch from API at localhost:8000
- [ ] No CORS errors in browser console
- [ ] API returns appropriate CORS headers

### 3. Database Connectivity

- [ ] API connects to SQLite database without errors
- [ ] Queries execute successfully
- [ ] Response times are under 500ms

### 4. Navigation

- [ ] Sidebar navigation works
- [ ] Click Overview → goes to /
- [ ] Click Activity → goes to /activity
- [ ] Click Analytics → goes to /analytics
- [ ] Click Settings → goes to /settings
- [ ] Back button works
- [ ] Page titles update correctly

## ✅ Performance Checks

- [ ] Home page loads in under 2 seconds
- [ ] Activity page loads in under 2 seconds
- [ ] Analytics charts render in under 1 second
- [ ] No browser lag when switching pages
- [ ] Network requests complete within reasonable time
- [ ] No memory leaks (check browser DevTools)

## ✅ Browser Console Checks

Open Developer Tools (F12):

- [ ] No red error messages
- [ ] No orange warning messages related to CORS
- [ ] No warnings about missing dependencies
- [ ] Network tab shows successful requests to API

## ✅ Mobile/Responsive (Optional)

- [ ] Dashboard works on mobile screen size (375px width)
- [ ] Sidebar might be hidden or scrollable
- [ ] Charts are readable on smaller screens
- [ ] Tables don't overflow without scrolling

## 📋 Final Verification Matrix

| Component | Status | Notes |
|-----------|--------|-------|
| Python Installed | ☐ Pass / ☐ Fail | |
| Node.js Installed | ☐ Pass / ☐ Fail | |
| API Server Starts | ☐ Pass / ☐ Fail | |
| Health Check | ☐ Pass / ☐ Fail | |
| / stats Endpoint | ☐ Pass / ☐ Fail | |
| / categories Endpoint | ☐ Pass / ☐ Fail | |
| / confidence Endpoint | ☐ Pass / ☐ Fail | |
| / activity Endpoint | ☐ Pass / ☐ Fail | |
| CORS Headers | ☐ Pass / ☐ Fail | |
| Dashboard Installs | ☐ Pass / ☐ Fail | |
| Dashboard Starts | ☐ Pass / ☐ Fail | |
| Home Page Loads | ☐ Pass / ☐ Fail | |
| Activity Page Loads | ☐ Pass / ☐ Fail | |
| Analytics Charts | ☐ Pass / ☐ Fail | |
| Settings Page | ☐ Pass / ☐ Fail | |
| Navigation Works | ☐ Pass / ☐ Fail | |
| Data Displays | ☐ Pass / ☐ Fail | |
| No Console Errors | ☐ Pass / ☐ Fail | |

## 🚀 Success!

If all checks pass, you have successfully:

✅ Extended Synapse with a FastAPI backend  
✅ Built a Next.js dashboard  
✅ Integrated real-time analytics  
✅ Configured system settings UI  

Your Synapse system is ready for use!

## 📞 Troubleshooting

### API Issues

**Port 8000 already in use:**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

**Import errors:**
```bash
pip install -r api/requirements.txt
```

**Database not found:**
- Ensure `organizer.db` exists in `d:\AUTOMATION\`
- Run `python -c "from storage import database; database.init_database()"`

### Dashboard Issues

**Port 3000 already in use:**
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

**npm install fails:**
```bash
rm -r node_modules package-lock.json
npm install
```

**API connection fails:**
- Check `.env.local` in dashboard folder
- Verify `NEXT_PUBLIC_API_URL=http://localhost:8000`
- Restart dashboard: `npm run dev`

### General

- Clear browser cache: Ctrl+Shift+Delete
- Check network tab (F12) for failed requests
- Verify both services running on correct ports
- Restart both services and try again
