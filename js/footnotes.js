/**
 * Leaderboard Footnotes Functionality
 * Auto-numbers footnotes and filters them based on visible rows
 */

// Footnote symbols (superscript numbers)
const FOOTNOTE_SYMBOLS = ['¹', '²', '³', '⁴', '⁵', '⁶', '⁷', '⁸', '⁹'];

/**
 * Initialize footnotes for all leaderboards
 */
document.addEventListener('DOMContentLoaded', () => {
    const leaderboards = getLeaderboardNames();
    leaderboards.forEach(leaderboard => {
        updateFootnotes(leaderboard);
    });
});

/**
 * Get all leaderboard names from embedded data
 */
function getLeaderboardNames() {
    const dataElement = document.getElementById('leaderboard-data');
    if (!dataElement) return [];

    const leaderboards = JSON.parse(dataElement.textContent);
    return leaderboards.map(lb => lb.name);
}

/**
 * Update footnotes for a specific leaderboard
 * Collects footnotes from visible rows, assigns numbers, and displays them
 */
function updateFootnotes(leaderboard) {
    const table = document.getElementById(`${leaderboard}-table`);
    const footnotesContainer = document.getElementById(`${leaderboard}-footnotes`);

    if (!table || !footnotesContainer) return;

    // Get all visible rows with footnotes
    const visibleRows = table.querySelectorAll('tbody tr.leaderboard-row:not(.hidden)');
    const footnotes = [];
    const footnoteMap = new Map(); // Map footnote text to number

    visibleRows.forEach(row => {
        const footnoteText = row.getAttribute('data-footnote');
        const footnoteRefSpan = row.querySelector('.footnote-ref');

        if (footnoteText && footnoteRefSpan) {
            // Check if this footnote already exists
            if (!footnoteMap.has(footnoteText)) {
                const footnoteNumber = footnotes.length + 1;
                footnoteMap.set(footnoteText, footnoteNumber);
                footnotes.push({
                    number: footnoteNumber,
                    text: footnoteText
                });
            }

            // Get the footnote number for this text
            const footnoteNumber = footnoteMap.get(footnoteText);
            const symbol = FOOTNOTE_SYMBOLS[footnoteNumber - 1] || `⁽${footnoteNumber}⁾`;

            // Update the footnote reference in the model name
            footnoteRefSpan.textContent = symbol;
            footnoteRefSpan.style.display = 'inline';
        } else if (footnoteRefSpan) {
            // Clear footnote reference if no footnote
            footnoteRefSpan.textContent = '';
            footnoteRefSpan.style.display = 'none';
        }
    });

    // Update footnotes display
    if (footnotes.length > 0) {
        footnotesContainer.innerHTML = footnotes.map(fn => {
            const symbol = FOOTNOTE_SYMBOLS[fn.number - 1] || `⁽${fn.number}⁾`;
            return `<p class="footnote-text">${symbol} ${fn.text}</p>`;
        }).join('');
        footnotesContainer.style.display = 'block';
    } else {
        footnotesContainer.innerHTML = '';
        footnotesContainer.style.display = 'none';
    }
}

/**
 * Export functions
 */
window.footnotes = {
    updateFootnotes
};
