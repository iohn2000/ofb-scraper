/**
 * Shared filter logic: club / team / year selectors, URL params, localStorage.
 * Loaded in base.html after the DOM elements it references.
 */

let _seasonsData = [];
let _clubsData = [];

function getUrlParam(key) {
    return new URLSearchParams(window.location.search).get(key);
}

function getSelectedClub() {
    return getUrlParam('club') || localStorage.getItem('selectedClub') || '1';
}

function getSelectedTeam() {
    return getUrlParam('team') || localStorage.getItem('selectedTeam') || 'U13';
}

function getSelectedYear() {
    return getUrlParam('year') || localStorage.getItem('selectedYear') || '2026';
}

/** Returns query string like "?club=1&team=U13&year=2026" */
function getTeamParams() {
    return '?club=' + encodeURIComponent(getSelectedClub())
        + '&team=' + encodeURIComponent(getSelectedTeam())
        + '&year=' + encodeURIComponent(getSelectedYear());
}

function populateClubDropdown(clubs) {
    _clubsData = clubs;
    const clubSelect = document.getElementById('clubSelect');
    const selectedClub = getSelectedClub();
    clubSelect.innerHTML = '';
    clubs.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = c.name;
        if (String(c.id) === String(selectedClub)) opt.selected = true;
        clubSelect.appendChild(opt);
    });
}

function populateDropdowns(seasons) {
    _seasonsData = seasons;
    const teamSelect = document.getElementById('teamSelect');

    const teams = [...new Set(seasons.map(s => s.age_group))].sort();
    const selectedTeam = getSelectedTeam();
    const selectedYear = getSelectedYear();

    teamSelect.innerHTML = '';
    teams.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t;
        opt.textContent = t;
        if (t === selectedTeam) opt.selected = true;
        teamSelect.appendChild(opt);
    });

    updateYearDropdown(selectedTeam, selectedYear);
}

function updateYearDropdown(team, selectedYear) {
    const yearSelect = document.getElementById('yearSelect');
    const dateRange = document.getElementById('seasonDateRange');
    const years = _seasonsData
        .filter(s => s.age_group === team)
        .map(s => s.season_year)
        .sort((a, b) => b - a);

    yearSelect.innerHTML = '';
    let matchedYear = false;
    years.forEach(y => {
        const opt = document.createElement('option');
        opt.value = y;
        opt.textContent = y;
        if (String(y) === String(selectedYear)) { opt.selected = true; matchedYear = true; }
        yearSelect.appendChild(opt);
    });
    if (!matchedYear && years.length > 0) {
        yearSelect.value = years[0];
    }

    const cur = _seasonsData.find(s => s.age_group === team && String(s.season_year) === String(yearSelect.value));
    if (cur) {
        dateRange.textContent = cur.date_from + ' → ' + cur.date_to;
    } else {
        dateRange.textContent = '';
    }
}

function onFilterChange() {
    const club = document.getElementById('clubSelect').value;
    const team = document.getElementById('teamSelect').value;
    const year = document.getElementById('yearSelect').value;
    localStorage.setItem('selectedClub', club);
    localStorage.setItem('selectedTeam', team);
    localStorage.setItem('selectedYear', year);
    const url = new URL(window.location);
    url.searchParams.set('club', club);
    url.searchParams.set('team', team);
    url.searchParams.set('year', year);
    window.location.href = url.toString();
}

// --- Event listeners ---
document.getElementById('clubSelect').addEventListener('change', onFilterChange);
document.getElementById('teamSelect').addEventListener('change', function() {
    updateYearDropdown(this.value, getSelectedYear());
    onFilterChange();
});
document.getElementById('yearSelect').addEventListener('change', onFilterChange);

// --- Load clubs and seasons on page load ---
Promise.all([
    fetch('/api/clubs').then(r => r.json()),
    fetch('/api/seasons').then(r => r.json())
]).then(([clubs, seasons]) => {
    populateClubDropdown(clubs);
    populateDropdowns(seasons);

    const club = getSelectedClub();
    const team = getSelectedTeam();
    const year = getSelectedYear();
    const clubObj = clubs.find(c => String(c.id) === String(club));
    const cur = seasons.find(s => s.age_group === team && String(s.season_year) === String(year));
    const dateStr = cur ? ' (' + cur.date_from + ' → ' + cur.date_to + ')' : '';
    const clubStr = clubObj ? clubObj.name + ' &middot; ' : '';

    const navbarClub = document.getElementById('navbar-club-name');
    if (navbarClub && clubObj) navbarClub.textContent = '· ' + clubObj.name;

    document.querySelectorAll('.team-season-info').forEach(el => {
        el.innerHTML = '<i class="fas fa-filter me-1"></i> <strong>' + clubStr + '</strong>'
            + '<strong>' + team + '</strong> &middot; Season <strong>' + year + '</strong>' + dateStr;
    });
}).catch(err => console.error('Failed to load filter data:', err));

// --- Mobile menu ---
function toggleMobileMenu() {
    const sidebar = document.getElementById('sidebarNav');
    sidebar.classList.toggle('show');

    const links = sidebar.querySelectorAll('.nav-link');
    links.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth < 1024) {
                sidebar.classList.remove('show');
            }
        });
    });
}

window.addEventListener('resize', () => {
    const sidebar = document.getElementById('sidebarNav');
    if (window.innerWidth >= 1024) {
        sidebar.classList.remove('show');
    }
});
