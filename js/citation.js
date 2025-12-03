/**
 * Citation copy and format switching functionality
 */

function initCitationCopy() {
    const copyBtns = document.querySelectorAll('.citation-container .copy-btn');

    copyBtns.forEach(btn => {
        const citationText = btn.closest('.citation-container').querySelector('pre');

        if (btn && citationText) {
            btn.addEventListener('click', function () {
                const textToCopy = citationText.textContent.trim();

                // Use modern clipboard API if available
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(textToCopy).then(() => {
                        showCopySuccess(btn);
                    }).catch(() => {
                        fallbackCopy(textToCopy, btn);
                    });
                } else {
                    fallbackCopy(textToCopy, btn);
                }
            });
        }
    });
}

function fallbackCopy(text, btn) {
    const tempElement = document.createElement('textarea');
    tempElement.value = text;
    tempElement.setAttribute('readonly', '');
    tempElement.style.position = 'absolute';
    tempElement.style.left = '-9999px';
    document.body.appendChild(tempElement);

    tempElement.select();
    document.execCommand('copy');
    document.body.removeChild(tempElement);

    showCopySuccess(btn);
}

function showCopySuccess(btn) {
    btn.classList.add('copy-success');
    btn.textContent = 'Copied!';

    setTimeout(function () {
        btn.classList.remove('copy-success');
        btn.textContent = 'Copy';
    }, 2000);
}

function initCitationFormatSwitcher() {
    // Hide all non-bibtex citation formats on load
    document.querySelectorAll('.citation-container').forEach(el => {
        if (!el.id.includes('-bibtex')) {
            el.classList.add('display-none');
        }
    });

    const formatButtons = document.querySelectorAll('.citation-format-btn');

    formatButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const format = this.getAttribute('data-format');
            const target = this.getAttribute('data-target');

            // Update button states
            const siblings = this.parentElement.querySelectorAll('.citation-format-btn');
            siblings.forEach(sib => sib.classList.remove('active'));
            this.classList.add('active');

            // Hide all containers for this target
            document.querySelectorAll(`[id^="${target}-"]`).forEach(el => {
                el.classList.add('display-none');
                el.classList.remove('display-block');
            });

            // Show the selected format
            const container = document.getElementById(`${target}-${format}`);
            if (container) {
                container.classList.remove('display-none');
                container.classList.add('display-block');
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', function () {
    initCitationCopy();
    initCitationFormatSwitcher();
});

