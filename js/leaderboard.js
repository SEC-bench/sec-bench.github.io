/**
 * Leaderboard Tab Switching and Table Rendering
 */

// Current active tab (will be set to first leaderboard)
let currentTab = null;

// Sort state (initially null, will be set on first sort)
let sortState = {
    column: null,
    direction: 'desc'
};

/**
 * Get first leaderboard name from embedded data
 */
function getFirstLeaderboardName() {
    const dataElement = document.getElementById('leaderboard-data');
    if (!dataElement) return null;

    const leaderboards = JSON.parse(dataElement.textContent);
    return leaderboards.length > 0 ? leaderboards[0].name : null;
}

/**
 * Initialize leaderboard functionality
 */
document.addEventListener('DOMContentLoaded', () => {
    // Set current tab to first leaderboard
    currentTab = getFirstLeaderboardName();

    initTabs();
    initSorting();

    // Sort by resolved (descending) on initial load
    if (currentTab) {
        sortTable(currentTab, 'resolved');
    }
});

/**
 * Initialize tab switching
 */
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tab = button.getAttribute('data-tab');
            switchTab(tab);
        });
    });
}

/**
 * Switch to a different tab
 */
function switchTab(tab) {
    if (tab === currentTab) return;

    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-tab') === tab);
    });

    // Update content visibility
    document.querySelectorAll('.leaderboard-content').forEach(content => {
        const contentTab = content.id.replace('-content', '');
        content.style.display = contentTab === tab ? 'block' : 'none';
    });

    currentTab = tab;

    // Reset sort state when switching tabs
    sortState = { column: 'resolved', direction: 'desc' };

    // Update rankings for the new tab
    updateRankings(tab);
}

/**
 * Initialize table sorting
 */
function initSorting() {
    const tables = document.querySelectorAll('.leaderboard-table');

    tables.forEach(table => {
        const headers = table.querySelectorAll('th.sortable');

        headers.forEach(header => {
            header.addEventListener('click', () => {
                const column = header.getAttribute('data-sort');
                const tableId = table.id;
                const leaderboardName = tableId.replace('-table', '');

                sortTable(leaderboardName, column);
            });
        });
    });
}

/**
 * Sort table by column
 */
function sortTable(leaderboardName, column) {
    const table = document.getElementById(`${leaderboardName}-table`);
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr.leaderboard-row'));

    // Determine sort direction
    let direction = 'desc'; // Default to descending for numeric columns
    if (sortState.column === column) {
        // Toggle direction if clicking same column
        direction = sortState.direction === 'asc' ? 'desc' : 'asc';
    } else if (column === 'model' || column === 'org' || column === 'date') {
        // Text/date columns default to ascending
        direction = 'asc';
    }

    // Update sort state
    sortState = { column, direction };

    // Update header classes
    table.querySelectorAll('th.sortable').forEach(th => {
        th.classList.remove('active', 'asc', 'desc');
        if (th.getAttribute('data-sort') === column) {
            th.classList.add('active', direction);
        }
    });

    // Sort rows
    rows.sort((a, b) => {
        let aValue = a.getAttribute(`data-${column}`);
        let bValue = b.getAttribute(`data-${column}`);

        // Convert to numbers if applicable
        if (!isNaN(aValue) && !isNaN(bValue)) {
            aValue = parseFloat(aValue);
            bValue = parseFloat(bValue);
        }

        if (aValue < bValue) return direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return direction === 'asc' ? 1 : -1;
        return 0;
    });

    // Re-append rows in sorted order
    rows.forEach(row => tbody.appendChild(row));

    // Update rankings
    updateRankings(leaderboardName);
}

/**
 * Update row rankings (visible only)
 */
function updateRankings(leaderboardName) {
    const table = document.getElementById(`${leaderboardName}-table`);
    const rows = table.querySelectorAll('tbody tr.leaderboard-row');

    let rank = 1;
    rows.forEach(row => {
        const rankCell = row.querySelector('.rank-col');
        if (!row.classList.contains('hidden')) {
            rankCell.textContent = rank++;
        } else {
            rankCell.textContent = '';
        }
    });
}

/**
 * Get visible row count for a leaderboard
 */
function getVisibleRowCount(leaderboardName) {
    const table = document.getElementById(`${leaderboardName}-table`);
    const rows = table.querySelectorAll('tbody tr.leaderboard-row:not(.hidden)');
    return rows.length;
}

/**
 * Export functions for use in other modules
 */
window.leaderboard = {
    updateRankings,
    getVisibleRowCount,
    currentTab: () => currentTab
};
