/**
 * Ranking page functionality
 * Fetches and displays B-Liga ranking data on-the-fly
 */

document.addEventListener('DOMContentLoaded', function() {
    const tableTypeButtons = document.querySelectorAll('.table-type-btn');
    
    // Load initial ranking when page loads
    loadRanking('NORMAL');
    
    // Load ranking when table type button is clicked
    tableTypeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const tableType = this.getAttribute('data-type');
            
            // Update button styling
            tableTypeButtons.forEach(b => {
                b.classList.remove('btn-primary');
                b.classList.add('btn-outline-primary');
            });
            this.classList.remove('btn-outline-primary');
            this.classList.add('btn-primary');
            
            // Load ranking
            loadRanking(tableType);
        });
    });
});

function loadRanking(tableType) {
    const team = getSelectedTeam();
    const loadingSpinner = document.getElementById('loadingSpinner');
    const errorAlert = document.getElementById('errorAlert');
    const rankingContainer = document.getElementById('rankingContainer');
    
    // Update page title
    document.getElementById('pageTitle').textContent = `${team} Ranking Season 25/26`;
    
    // Show loading state
    loadingSpinner.classList.remove('d-none');
    errorAlert.classList.add('d-none');
    rankingContainer.classList.add('d-none');
    
    // Fetch ranking data from API
    const params = new URLSearchParams({
        team: team,
        table_type: tableType
    });
    
    fetch(`/api/ranking?${params}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            loadingSpinner.classList.add('d-none');
            
            if (data.error) {
                showError(data.error);
                return;
            }
            
            if (!data.success) {
                showError('Failed to fetch ranking data');
                return;
            }
            
            displayRanking(data);
            rankingContainer.classList.remove('d-none');
        })
        .catch(error => {
            loadingSpinner.classList.add('d-none');
            showError(`Failed to load ranking: ${error.message}`);
        });
}

function displayRanking(data) {
    const tableTypeName = getTableTypeLabel(data.table_type);
    document.getElementById('liganName').textContent = data.liga_name;
    document.getElementById('tableTypeName').textContent = tableTypeName;
    
    const tbody = document.getElementById('rankingTableBody');
    tbody.innerHTML = '';
    
    data.entries.forEach(entry => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="fw-bold">${entry.rang}</td>
            <td>${entry.mannschaftBezeichnung}</td>
            <td class="text-center">${entry.spiele}</td>
            <td class="text-center">${entry.siege}</td>
            <td class="text-center">${entry.unentschieden}</td>
            <td class="text-center">${entry.niederlagen}</td>
            <td class="text-center">${entry.toreErzielt}:${entry.toreErhalten}</td>
            <td class="text-center ${entry.tordifferenz >= 0 ? 'text-success' : 'text-danger'}">
                ${entry.tordifferenz > 0 ? '+' : ''}${entry.tordifferenz}
            </td>
            <td class="fw-bold text-center text-primary">${entry.punkte}</td>
        `;
        tbody.appendChild(row);
    });
}

function showError(message) {
    const errorAlert = document.getElementById('errorAlert');
    errorAlert.textContent = `Error: ${message}`;
    errorAlert.classList.remove('d-none');
}

function getTableTypeLabel(tableType) {
    const labels = {
        'NORMAL': 'Gesamt (Overall)',
        'HEIM': 'Heim (Home)',
        'AUSWAERTS': 'Auswärts (Away)',
        'HERBST': 'Herbst (Fall)',
        'FRUEHJAHR': 'Frühjahr (Spring)'
    };
    return labels[tableType] || tableType;
}
