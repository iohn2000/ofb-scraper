# Quick Start Guide - Windows PowerShell

## Prerequisites Check
Before starting, ensure:
1. Docker Desktop is installed and running
2. You're in the `c:\dev\ofb-scraper` directory
3. `ofb_stats.db` exists (the database with player stats)

## Step 1: Start Docker Container

```powershell
# Navigate to project directory (if not already there)
cd c:\dev\ofb-scraper

# Build and run the Docker container with hot-reload
docker-compose up --build
```

Output should look like:
```
web  | WARNING: This is a development server...
web  |  * Running on http://0.0.0.0:5000
```

**Do NOT close this terminal** - keep it running while you work.

## Step 2: Open Website

1. Open your web browser (Chrome, Firefox, Edge, Safari, etc.)
2. Go to: http://localhost:5000
3. You should see the "Total Minutes Played by Player" chart

## Step 3: Test Navigation

Click the menu items on the left:
- ✓ **Minutes Played** (chart should display)
- ✓ **Goals Scored** (chart should display)  
- ✓ **Efficiency Stats** (table should display)

## Step 4: Test Responsive Design

1. Open Browser DevTools: Press **F12**
2. Click "Toggle device toolbar": **Ctrl+Shift+M**
3. Select device presets:
   - **iPhone 12** (mobile) - should stack vertically
   - **iPad** (tablet) - should still show sidebar
   - **Desktop** (1024x768) - full layout

## Step 5: Test Hot-Reload (Live Code Updates)

### Backend Python Hot-Reload:
1. Open `backend/app.py` in VS Code
2. Change something, e.g., line 13:
   ```python
   # Change from:
   def index():
   # To:
   def index():
       # Added comment
   ```
3. Save the file
4. Go back to browser, press **F5** (refresh)
5. ✓ Should work without restarting Docker

### Frontend HTML Hot-Reload:
1. Open `frontend/templates/minutes_chart.html` in VS Code
2. Find line with `<h1>` and add text:
   ```html
   <!-- Change from: -->
   <h1 class="mb-4">
   <!-- To: -->
   <h1 class="mb-4" style="color: red;">
   ```
3. Save the file
4. Go to browser, press **Ctrl+Shift+R** (hard refresh)
5. ✓ Should see the h1 text in red

## Step 6: Stop Container (When Done)

In PowerShell, press **Ctrl+C** to stop the running container.

Or in a new PowerShell window, run:
```powershell
docker-compose down
```

## Common Issues & Fixes

### Port 5000 Already in Use
```powershell
# Option 1: Use different port, edit docker-compose.yml line 8:
# Change: - "5000:5000"
# To:     - "5001:5000"
# Then: docker-compose up --build

# Option 2: Kill existing process on port 5000
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force
docker-compose up --build
```

### Database File Not Found
```powershell
# Check if ofb_stats.db exists
Test-Path ofb_stats.db

# If missing, create from scraper (if available)
python scrape_two_step.py
```

### Charts Not Loading
1. Open Browser DevTools (**F12**)
2. Go to **Console** tab
3. Check for red error messages
4. Check **Network** tab - API calls should return 200 status
5. Try: http://localhost:5000/api/minutes in browser address bar

### Container Crashes on Start
```powershell
# Check logs
docker-compose logs web

# Common fix: rebuild everything
docker-compose down
Remove-Item -Recurse docker_compose_cache 2>$null
docker system prune -a -f
docker-compose up --build
```

## Quick Command Reference

```powershell
# Start container
docker-compose up --build

# Stop container
docker-compose down

# View logs
docker-compose logs -f web

# Restart without rebuild
docker-compose up

# Remove all Docker data (WARNING: destructive)
docker system prune -a -f

# Check if container is running
docker ps

# SSH into container (for debugging)
docker-compose exec web bash
```

## File Locations

| What | Where |
|------|-------|
| Backend code | `backend/app.py`, `backend/utils/queries.py` |
| HTML pages | `frontend/templates/*.html` |
| Styling | `frontend/static/css/style.css` |
| Database | `ofb_stats.db` |
| Config | `docker-compose.yml` |

## Visual Site Layout

```
┌─────────────────────────────────────────┐
│              Minutes Played             │
├──────────────┬──────────────────────────┤
│   SIDEBAR    │  CHART CONTENT           │
│              │                          │
│ ✓ Minutes   │  [Horizontal bar chart]  │
│ ✓ Goals     │  [Player 1: 500]         │
│ ✓ Efficiency│  [Player 2: 450]         │
│              │  [Player 3: 400]         │
└──────────────┴──────────────────────────┘
```

## Next Steps

1. Run `docker-compose up --build`
2. Wait for "Running on http://0.0.0.0:5000"
3. Open http://localhost:5000
4. Explore the three stat pages
5. Test on mobile view with DevTools
6. Make code changes and verify hot-reload works

For detailed documentation, see: `DOCKER_README.md`
