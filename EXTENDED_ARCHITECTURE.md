# 🧠 SYNAPSE - Extended Architecture Guide

## System Components

### 1. Backend (Python)

**Core System** (`core/`, `ai/`, `storage/`)
- Real-time file watchdog monitoring
- AI-based semantic classification
- SQLite decision logging
- Safety guardrails

### 2. API Layer (FastAPI)

**New Component** - `api/server.py`
- RESTful endpoints for analytics
- CORS-enabled for dashboard integration
- Endpoints:
  - `/stats` - System statistics
  - `/categories` - Category distribution
  - `/confidence` - Confidence metrics
  - `/activity` - File decision log
  - `/summary` - Complete overview

### 3. Dashboard (Next.js)

**New Component** - `dashboard/`
- Pages: Overview, Activity, Analytics, Settings
- Real-time data visualization
- Tailwind CSS styling
- Recharts for analytics

## Setup Instructions

### Step 1: Install API Dependencies

```bash
pip install -r api/requirements.txt
```

Or manually:
```bash
pip install fastapi uvicorn
```

### Step 2: Start the API Server

```bash
cd d:\AUTOMATION
python -m uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

Server will be at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### Step 3: Set Up Dashboard

```bash
cd dashboard
npm install
```

### Step 4: Configure Dashboard

Create `.env.local` in `dashboard/`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 5: Start Dashboard

```bash
cd dashboard
npm run dev
```

Dashboard will be at: `http://localhost:3000`

## File Structure

```
d:\AUTOMATION\
├── api/
│   ├── __init__.py
│   ├── server.py          # FastAPI application
│   └── requirements.txt    # Python dependencies
│
├── dashboard/
│   ├── app/
│   │   ├── layout.tsx     # Root layout
│   │   ├── page.tsx       # Home/Overview
│   │   ├── activity/      # Activity page
│   │   ├── analytics/     # Analytics page
│   │   ├── settings/      # Settings page
│   │   └── globals.css    # Global styles
│   ├── components/        # Reusable components
│   ├── lib/
│   │   └── api.ts         # API client
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   └── README.md
│
├── core/                  # Existing
├── ai/                    # Existing
├── storage/               # Existing
└── app/                   # Existing
```

## API Endpoints Reference

### Statistics & Analytics

```
GET /stats
Response:
{
  "total_files": 1420,
  "today_files": 128,
  "status": "operational",
  "timestamp": "2026-03-05T10:30:00"
}

GET /categories
Response:
{
  "categories": [
    {"category": "COLLEGE", "count": 450},
    {"category": "PROGRAMMING", "count": 380},
    ...
  ],
  "total": 1420
}

GET /confidence
Response:
{
  "distribution": [
    {"bucket": "high", "count": 1200},
    {"bucket": "medium", "count": 180},
    {"bucket": "low", "count": 40}
  ],
  "total": 1420
}

GET /summary
Response:
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

### Activity & Decisions

```
GET /activity?limit=50
Response:
{
  "activity": [
    {
      "timestamp": "2026-03-05T10:30:00",
      "file_name": "CPU Scheduling.pdf",
      "category": "COLLEGE",
      "confidence": 0.92,
      "action": "moved",
      "destination": "D:/01_COLLEGE/Operating Systems/..."
    },
    ...
  ],
  "count": 50
}

GET /activity/today
Response:
{
  "activity": [... today's decisions only ...],
  "count": 28
}

GET /activity/file/{file_name}
Response:
{
  "file_name": "CPU Scheduling.pdf",
  "activity": [... all decisions for this file ...],
  "count": 3
}
```

### Configuration

```
GET /settings
Response:
{
  "confidence_thresholds": {
    "high": 0.8,
    "medium": 0.6,
    "low": 0.4
  },
  "preview_mode": false,
  "auto_mode": true,
  "monitoring_enabled": true
}

POST /settings
Body:
{
  "confidence_thresholds": {
    "high": 0.85,
    "medium": 0.65,
    "low": 0.45
  }
}
```

## Dashboard Pages

### Home (/)
- Total files organized
- Files organized today
- System status
- Recent activity table
- Quick stats cards

### Activity (/activity)
- Full decision log table
- Sortable columns
- Filter by action, category, confidence
- Inline confidence visualization
- Activity summary

### Analytics (/analytics)
- Category distribution bar chart
- Confidence distribution pie chart
- Detailed statistics table
- Trend analysis

### Settings (/settings)
- Confidence threshold sliders
- Operation mode toggles
- Preview mode activation
- Monitoring settings
- Save configuration

## Integration Points

### How They Work Together

1. **Synapse Core** (unchanged)
   - Monitors files in real-time
   - Classifies and moves files
   - Logs decisions to SQLite

2. **API Server**
   - Reads from SQLite database
   - Exposes data via REST API
   - Handles CORS for dashboard

3. **Dashboard**
   - Fetches data from API
   - Displays real-time analytics
   - Allows configuration changes

## Running Everything

### Option 1: One Terminal (Sequential)

```bash
# Terminal 1: Start API
cd d:\AUTOMATION
python -m uvicorn api.server:app --reload

# Terminal 2: Start Dashboard
cd d:\AUTOMATION\dashboard
npm run dev

# Terminal 3: Start Synapse Core (if needed)
cd d:\AUTOMATION
# Follow existing core startup procedure
```

### Option 2: Multiple Terminals (Parallel)

Run each in a separate terminal:

```bash
# Terminal 1: Core Synapse
cd d:\AUTOMATION
python -m app.main

# Terminal 2: API Server
cd d:\AUTOMATION
python -m uvicorn api.server:app --reload

# Terminal 3: Dashboard
cd d:\AUTOMATION\dashboard
npm run dev
```

## Performance Considerations

### Caching Strategy

- Stats: 10-second cache
- Categories: 10-second cache
- Activity: 5-second cache
- Settings: 60-second cache

### Database Optimization

- SQLite with WAL mode enabled
- Indexed queries on timestamp and category
- Connection pooling ready
- Batch operations supported

### Frontend Optimization

- Next.js automatic code splitting
- Image optimization
- CSS minification
- Tailwind purging

## Troubleshooting

### "API connection refused"
- Verify API server is running: `http://localhost:8000/health`
- Check firewall settings
- Ensure CORS middleware is active

### "Dashboard shows 'Loading...'"
- Check browser console for errors (F12)
- Verify `.env.local` has correct API URL
- Check network tab in DevTools

### "Charts not displaying"
- Clear browser cache
- Verify Recharts is installed: `npm list recharts`
- Check console for JavaScript errors

### "No data appearing"
- Verify Synapse core is logging decisions
- Check SQLite database exists: `organizer.db`
- Test API directly: `curl http://localhost:8000/stats`

## Security Notes

- Dashboard currently has no authentication
- Add authentication before production use
- API has CORS enabled for localhost only
- SQLite connection uses `check_same_thread=False` for multi-threading
- All database queries use parameterized statements

## Future Enhancements

- [ ] Real-time WebSocket updates
- [ ] User authentication via JWT
- [ ] Custom date range filtering
- [ ] Export reports as PDF/CSV
- [ ] Mobile responsive dashboard
- [ ] Dark/Light theme toggle
- [ ] Advanced analytics (ML predictions)
- [ ] Webhook integrations

## Support

For issues or questions:
1. Check API documentation: `http://localhost:8000/docs`
2. Review database queries in `storage/database.py`
3. Check dashboard logs in browser console
4. Verify all services are running on correct ports
