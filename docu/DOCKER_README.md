# ÖFB U13 Player Statistics Dashboard

A Docker-based web application for visualizing player statistics from the ÖFB U13 team using Flask backend and responsive Bootstrap frontend.

## Features

- **Minutes Chart**: Horizontal bar chart showing total minutes played per player
- **Goals Chart**: Horizontal bar chart showing total goals scored per player
- **Efficiency Stats**: Table showing comprehensive efficiency metrics (goals/90min, min/goal, etc.)
- **Responsive Design**: Works on mobile phones, tablets, and desktops
- **Hot-Reload Development**: Automatic code updates when files are modified (no container restart needed)
- **Left-Side Navigation**: Easy access to all stat pages

## Prerequisites

- Docker Desktop installed and running
- Windows, Mac, or Linux with PowerShell or Bash terminal access
- Database file: `ofb_stats.db` (should be in the project root)

## Quick Start

### 1. Build and Run Docker Container

From the project root directory:

```bash
docker-compose up --build
```

This will:
- Build the Flask application image
- Start the web server on http://localhost:5000
- Create volume mounts for hot-reload development

### 2. Access the Website

Open your browser and navigate to:
```
http://localhost:5000
```

You should see the minutes chart page with the sidebar navigation menu.

### 3. Navigate Between Pages

Use the left sidebar menu to access:
- **Minutes Played**: View total minutes per player
- **Goals Scored**: View total goals per player
- **Efficiency Stats**: View detailed efficiency metrics

## Development Workflow

### Hot-Reload (Auto-Refresh)

Changes to backend code are automatically reflected without restarting the container:

1. **Edit backend Python files** (e.g., `backend/app.py`, `backend/utils/queries.py`)
   - Save the file
   - Refresh your browser - changes appear immediately

2. **Edit frontend HTML/CSS/JavaScript**
   - Save the file
   - Hard-refresh your browser (Ctrl+F5 or Cmd+Shift+R) - changes appear immediately

### Common Tasks

#### Stop the Container
```bash
docker-compose down
```

#### View Container Logs
```bash
docker-compose logs -f web
```

#### Rebuild After Dependency Changes
```bash
docker-compose up --build
```

#### Access Container Shell (for debugging)
```bash
docker-compose exec web bash
python
```

## Project Structure

```
ofb-scraper/
├── Dockerfile                          # Docker image definition
├── docker-compose.yml                  # Container orchestration
├── requirements.txt                    # Python dependencies
├── ofb_stats.db                        # SQLite database (volume mount)
├── backend/
│   ├── app.py                         # Flask application & routes
│   ├── utils/
│   │   ├── __init__.py
│   │   └── queries.py                 # Database query functions
└── frontend/
    ├── static/
    │   ├── css/
    │   │   └── style.css              # Responsive styling
    │   └── js/
    │       └── (placeholder for future JS)
    └── templates/
        ├── base.html                  # Base layout with navigation
        ├── minutes_chart.html         # Minutes chart page
        ├── goals_chart.html           # Goals chart page
        └── efficiency.html            # Efficiency stats page
```

## API Endpoints

The Flask backend provides the following JSON API endpoints:

- `GET /api/minutes` - Returns player minutes data
- `GET /api/goals` - Returns player goals data
- `GET /api/efficiency` - Returns player efficiency statistics

These are consumed by the frontend to render charts and tables.

## Responsive Breakpoints

The website is designed for:
- **Mobile**: < 576px (extra small phones)
- **Small Mobile**: 576px - 767px (phones)
- **Tablet**: 768px - 1023px
- **Desktop**: > 1024px

Test on different devices using Chrome DevTools:
1. Open DevTools (F12)
2. Click device toolbar icon (Ctrl+Shift+M)
3. Select various device presets (iPhone, iPad, Desktop)

## Database

The application reads from `ofb_stats.db` (SQLite) which contains:
- `players` table: Player information
- `games` table: Game statistics (minutes played, goals, etc.)

The database is mounted as read-only in Docker for safety.

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs web

# Rebuild
docker-compose down
docker-compose up --build
```

### Port 5000 already in use
```bash
# Change port in docker-compose.yml
# Line: ports: - "5000:5000"
# Change first 5000 to different port, e.g., "5001:5000"
```

### Database not found
Ensure `ofb_stats.db` exists in the project root directory:
```bash
ls -la ofb_stats.db
```

### Charts not loading
- Check browser console (F12 → Console) for errors
- Verify API endpoints respond: http://localhost:5000/api/minutes
- Ensure database has data

## Performance Notes

- Chart.js renders efficiently on mobile devices
- Bootstrap 5 provides lightweight responsive framework
- Flask development server is suitable for team usage; for production, use Gunicorn or similar

## Future Enhancements

- Add dark/light theme toggle
- Export charts as PNG/PDF
- Add more statistical views
- Implement data filtering and date ranges
- Add player search functionality
