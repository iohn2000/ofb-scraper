# Project Structure Guide

```
ofb-scraper/                           ← Project root
│
├── README.md                           ← Original project README
├── QUICK_START.md                      ← Windows quick start guide ⭐ START HERE
├── DOCKER_README.md                    ← Detailed Docker documentation
├── docker-compose.yml                  ← Docker container configuration
├── Dockerfile                          ← Docker image definition
├── .dockerignore                       ← Files to exclude from Docker build
├── requirements.txt                    ← Python dependencies (updated)
│
├── ofb_stats.db                        ← SQLite database (read-only in Docker)
├── scrape_two_step.py                  ← Original scraper (standalone)
│
├── backend/                            ← Backend application (Flask)
│   ├── app.py                          ← Main Flask app with routes
│   └── utils/
│       ├── __init__.py
│       └── queries.py                  ← Database query functions
│
├── frontend/                           ← Frontend application (HTML/CSS/JS)
│   ├── static/                         ← Static assets
│   │   ├── css/
│   │   │   └── style.css              ← Responsive CSS (mobile-first)
│   │   └── js/
│   │       └── (placeholder)
│   └── templates/                      ← HTML templates
│       ├── base.html                  ← Base layout with sidebar nav
│       ├── minutes_chart.html         ← Minutes chart page
│       ├── goals_chart.html           ← Goals chart page
│       └── efficiency.html            ← Efficiency stats table
│
└── (other files)                       ← Query scripts, debug files, etc.
```

## File Purposes

### Configuration Files
- **docker-compose.yml** - Defines the web service, port mapping, volume mounts for hot-reload
- **Dockerfile** - Build instructions for Python 3.11 + Flask + dependencies
- **.dockerignore** - Excludes unnecessary files from Docker image (keeps it small)
- **requirements.txt** - Python package dependencies (Flask, requests, etc.)

### Backend Application
- **backend/app.py** - Flask application with 6 routes:
  - `/` - Minutes chart page
  - `/goals` - Goals chart page  
  - `/efficiency` - Efficiency stats page
  - `/api/minutes` - JSON API for minutes data
  - `/api/goals` - JSON API for goals data
  - `/api/efficiency` - JSON API for efficiency data

- **backend/utils/queries.py** - Database query functions that fetch data from `ofb_stats.db`:
  - `get_player_minutes()` - Aggregates total minutes per player
  - `get_player_goals()` - Aggregates total goals per player
  - `get_player_efficiency()` - Calculates efficiency metrics per player

### Frontend Application
- **frontend/templates/base.html** - Base layout template with:
  - Left sidebar navigation (fixed on desktop, hamburger on mobile)
  - Main content area (flex layout)
  - Bootstrap 5 + Chart.js imports
  - Responsive viewport configuration
  - Navigation active state highlighting via Jinja2

- **frontend/templates/*_chart.html** - Chart pages with:
  - Extends base.html for consistent layout
  - Canvas element for Chart.js
  - Fetch API call to backend API endpoint
  - Chart.js configuration (bar chart, responsive, data labels)

- **frontend/templates/efficiency.html** - Table page with:
  - Responsive table with Bootstrap styling
  - Fetches JSON from API
  - Dynamic row generation via JavaScript
  - Badges for visual emphasis on key metrics

- **frontend/static/css/style.css** - Responsive CSS with:
  - CSS Variables for theming
  - Sidebar styling (fixed on desktop, offcanvas on mobile)
  - Responsive breakpoints: 576px, 768px, 1024px
  - Mobile-first design approach
  - Chart container sizing
  - Table responsive scrolling on mobile

## How Data Flows

```
1. User visits http://localhost:5000
2. Flask serves base.html + page template (e.g., minutes_chart.html)
3. Browser renders HTML with Chart.js canvas
4. JavaScript code in template runs fetch('/api/minutes')
5. Flask route /api/minutes calls queries.py function
6. Query function connects to ofb_stats.db and executes SQL
7. Results returned as JSON to browser
8. Chart.js renders data in canvas element
9. User sees interactive chart on responsive layout
```

## Hot-Reload Mechanism

Volume Mounts in docker-compose.yml enable:
- `/backend:/app/backend` - Python file changes trigger Flask auto-reload
- `/frontend/templates:/app/frontend/templates` - HTML changes visible on refresh
- `/frontend/static:/app/frontend/static` - CSS/JS changes visible on refresh
- `/ofb_stats.db:/app/ofb_stats.db:ro` - Database file (read-only)

Flask runs with `FLASK_ENV=development` which enables:
- Auto-reload on Python file changes
- Debug mode with detailed error pages
- Debugger accessible on errors

## Responsive Breakpoints

**Mobile-First Approach:**
- **Extra Small (<576px)**: Full-width, hamburger menu
- **Small (576-767px)**: Stack layout, vertical navigation
- **Tablet (768-1023px)**: Sidebar transforms to left panel, charts resize
- **Desktop (>1024px)**: Full sidebar, max chart dimensions

## Technology Stack

- **Backend**: Python 3.11 + Flask 2.3.0 + Werkzeug
- **Frontend**: HTML5 + Bootstrap 5.3.0 + Chart.js 4.3.0
- **Database**: SQLite (ofb_stats.db)
- **Container**: Docker + Docker Compose
- **Templating**: Jinja2 (Flask built-in)
- **HTTP**: Standard HTTP/JSON APIs

## Data Sources

All visualization data comes from `ofb_stats.db` which contains:
- **players** table: player_id, player_name, team, season_year
- **games** table: game statistics per player (minutes_played, goals, competition, etc.)

Queries aggregate this data with SQL GROUP BY and SUM operations.

## Adding New Pages

To add a new stat page:

1. Create `frontend/templates/newpage.html` (extends base.html)
2. Add new function in `backend/utils/queries.py` (e.g., `get_new_stat()`)
3. Add new route in `backend/app.py`:
   ```python
   @app.route('/newpage')
   def newpage():
       return render_template('newpage.html')
   
   @app.route('/api/newstat')
   def api_newstat():
       data = get_new_stat(DB_PATH)
       return jsonify(data)
   ```
4. Add navigation link in `frontend/templates/base.html`:
   ```html
   <li class="nav-item">
       <a class="nav-link" href="/newpage">New Page</a>
   </li>
   ```
5. Refresh browser - page appears in menu!

## Development Workflow

```
1. Start: docker-compose up --build
2. Work: Edit code in VS Code (backend/, frontend/)
3. Test: Refresh browser or check auto-reload
4. Deploy: Push to production (simple Flask setup)
5. Stop: docker-compose down
```

---

**Status**: ✅ Complete - Ready to run!
**Command**: `docker-compose up --build`
**URL**: http://localhost:5000
