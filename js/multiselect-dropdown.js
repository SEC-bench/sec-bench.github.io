/**
 * Multi-Select Dropdown Component (similar to SWE-bench)
 * Supports search, multiple selection, and "All" option
 */

class MultiSelectDropdown {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container ${containerId} not found`);
            return;
        }

        this.options = options;
        this.items = options.items || [];
        this.selectedItems = new Set(options.selected || []);
        this.displayName = options.displayName || 'Items';
        this.onSelectionChange = options.onSelectionChange || (() => {});
        this.searchEnabled = options.searchEnabled !== false;

        this.isOpen = false;
        this.render();
        this.attachEventListeners();
    }

    render() {
        const selectedCount = this.selectedItems.has('all') ?
            'All' :
            (this.selectedItems.size === 0 ? 'None' : this.selectedItems.size);

        const html = `
            <div class="multiselect-wrapper">
                <button class="multiselect-toggle" type="button">
                    <span class="multiselect-label">${this.displayName}: ${selectedCount}</span>
                    <svg class="multiselect-arrow" width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                        <path d="M6 8L2 4h8L6 8z"/>
                    </svg>
                </button>
                <div class="multiselect-dropdown" style="display: none;">
                    ${this.searchEnabled ? `
                        <div class="multiselect-search-container">
                            <input type="text"
                                   class="multiselect-search"
                                   placeholder="Search..."
                                   autocomplete="off">
                        </div>
                    ` : ''}
                    <div class="multiselect-options">
                        <label class="multiselect-option">
                            <input type="checkbox"
                                   value="all"
                                   ${this.selectedItems.has('all') ? 'checked' : ''}>
                            <span class="multiselect-option-text">All ${this.displayName}</span>
                        </label>
                        ${this.items.map(item => `
                            <label class="multiselect-option" data-search-text="${item.toLowerCase()}">
                                <input type="checkbox"
                                       value="${item}"
                                       ${this.selectedItems.has(item) || this.selectedItems.has('all') ? 'checked' : ''}>
                                <span class="multiselect-option-text">${item}</span>
                            </label>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        this.container.innerHTML = html;
    }

    attachEventListeners() {
        // Toggle dropdown
        const toggle = this.container.querySelector('.multiselect-toggle');
        toggle.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown();
        });

        // Handle checkbox changes
        const checkboxes = this.container.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                this.handleCheckboxChange(e.target);
            });
        });

        // Handle search
        if (this.searchEnabled) {
            const searchInput = this.container.querySelector('.multiselect-search');
            searchInput.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });
            searchInput.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target) && this.isOpen) {
                this.closeDropdown();
            }
        });
    }

    toggleDropdown() {
        this.isOpen = !this.isOpen;
        const dropdown = this.container.querySelector('.multiselect-dropdown');
        const arrow = this.container.querySelector('.multiselect-arrow');

        dropdown.style.display = this.isOpen ? 'block' : 'none';
        arrow.style.transform = this.isOpen ? 'rotate(180deg)' : 'rotate(0deg)';

        if (this.isOpen && this.searchEnabled) {
            // Focus search input when opened
            setTimeout(() => {
                const searchInput = this.container.querySelector('.multiselect-search');
                if (searchInput) searchInput.focus();
            }, 100);
        }
    }

    closeDropdown() {
        this.isOpen = false;
        const dropdown = this.container.querySelector('.multiselect-dropdown');
        const arrow = this.container.querySelector('.multiselect-arrow');

        dropdown.style.display = 'none';
        arrow.style.transform = 'rotate(0deg)';
    }

    handleCheckboxChange(checkbox) {
        const value = checkbox.value;

        if (value === 'all') {
            if (checkbox.checked) {
                // Select all
                this.selectedItems = new Set(['all']);
                const allCheckboxes = this.container.querySelectorAll('input[type="checkbox"]');
                allCheckboxes.forEach(cb => cb.checked = true);
            } else {
                // Deselect all
                this.selectedItems.clear();
                const allCheckboxes = this.container.querySelectorAll('input[type="checkbox"]');
                allCheckboxes.forEach(cb => cb.checked = false);
            }
        } else {
            const allCheckbox = this.container.querySelector('input[value="all"]');

            if (checkbox.checked) {
                this.selectedItems.add(value);
                // Remove 'all' if it was selected
                if (this.selectedItems.has('all')) {
                    this.selectedItems.delete('all');
                }
                allCheckbox.checked = false;
            } else {
                this.selectedItems.delete(value);
                // Allow empty selection - don't auto-select 'all'
            }
        }

        this.updateToggleLabel();
        this.onSelectionChange(this.getSelectedItems());
    }

    handleSearch(query) {
        const options = this.container.querySelectorAll('.multiselect-option[data-search-text]');
        const searchTerm = query.toLowerCase().trim();

        options.forEach(option => {
            const searchText = option.getAttribute('data-search-text');
            if (searchText.includes(searchTerm)) {
                option.style.display = 'flex';
            } else {
                option.style.display = 'none';
            }
        });
    }

    updateToggleLabel() {
        const label = this.container.querySelector('.multiselect-label');
        const selectedCount = this.selectedItems.has('all') ?
            'All' :
            (this.selectedItems.size === 0 ? 'None' : this.selectedItems.size);

        label.textContent = `${this.displayName}: ${selectedCount}`;
    }

    getSelectedItems() {
        if (this.selectedItems.has('all')) {
            return new Set(['all']);
        }
        return new Set(this.selectedItems);
    }

    setSelectedItems(items) {
        this.selectedItems = new Set(items);
        this.render();
        this.attachEventListeners();
    }
}

// Export for use in other modules
window.MultiSelectDropdown = MultiSelectDropdown;
