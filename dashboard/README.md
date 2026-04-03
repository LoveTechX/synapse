# Synapse Dashboard README

## 🧠 SYNAPSE Dashboard

AI Workspace Intelligence - Real-time analytics and configuration dashboard for the Synapse file organization system.

### Quick Start

#### 1. Install Dependencies

```bash
cd dashboard
npm install
```

#### 2. Start API Server (in separate terminal)

```bash
cd ..
pip install fastapi uvicorn
python -m uvicorn api.server:app --reload
```

The API should now be available at `http://localhost:8000`

#### 3. Start Dashboard

```bash
cd dashboard
npm run dev
```

The dashboard will be available at `http://localhost:3000`

### Features

- **📊 Overview Dashboard** - Real-time statistics and recent activity
- **📈 Analytics** - Category distribution and confidence scoring charts
- **📋 Activity Log** - Detailed view of all file decisions
- **⚙️ Settings** - Configure confidence thresholds and operation modes

### API Endpoints

```
GET  /stats              # System statistics
GET  /categories         # Category distribution
GET  /confidence         # Confidence distribution
GET  /activity           # Recent file decisions
GET  /activity/today     # Today's decisions
GET  /summary            # Complete system summary
GET  /settings           # System configuration
POST /settings           # Update configuration
```

### Tech Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Charts**: Recharts
- **Backend**: FastAPI, Python
- **Database**: SQLite (via Synapse backend)

### Development

```bash
# Start development server with hot reload
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint
npm run lint
```

### Environment Variables

Create `.env.local` file:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Production Build

```bash
npm run build
npm start
```

Server will start on `http://localhost:3000`

### Troubleshooting

**Dashboard won't load?**
- Check that the API server is running on `http://localhost:8000`
- Verify CORS is enabled in API (should be by default)

**API connection error?**
- Set `NEXT_PUBLIC_API_URL` environment variable
- Ensure FastAPI server is running

**Charts not rendering?**
- Clear browser cache
- Restart Next.js dev server

### Architecture

```
dashboard/
├── app/
│   ├── layout.tsx         # Root layout with sidebar
│   ├── page.tsx           # Home/overview page
│   ├── activity/
│   │   └── page.tsx       # Activity log
│   ├── analytics/
│   │   └── page.tsx       # Charts and analytics
│   ├── settings/
│   │   └── page.tsx       # Configuration
│   └── globals.css        # Global styles
├── components/
│   ├── Sidebar.tsx        # Navigation sidebar
│   ├── Header.tsx         # Page header
│   └── StatCard.tsx       # Stat card component
├── lib/
│   └── api.ts             # API client
└── package.json
```

### Performance Tips

- API responses are cached with NextJS `revalidate`
- Statistics refresh every 10 seconds
- Activity logs refresh every 5 seconds
- Use `/activity/today` for today's data instead of full log

### Future Enhancements

- [ ] Real-time WebSocket updates
- [ ] Custom date range selection
- [ ] Export analytics to CSV
- [ ] User authentication
- [ ] Dark/Light theme toggle
- [ ] Mobile responsive improvements
