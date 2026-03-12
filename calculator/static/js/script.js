/**
 * =============================================================================
 * script.js - Frontend Logic for SmartCalc
 * =============================================================================
 * Handles display updates, button clicks, keyboard events, and 
 * communication with the Flask backend API.
 * =============================================================================
 */

// Global State
const display = document.getElementById('calc-display');
const historyList = document.getElementById('history-list');
const themeToggle = document.getElementById('theme-toggle');
const themeIcon = document.getElementById('theme-icon');

/**
 * Appends a value to the calculator display.
 * @param {string} value - The character or function string to append.
 */
function append(value) {
    if (display.value === '0' && value !== '.') {
        display.value = value;
    } else {
        display.value += value;
    }
}

/**
 * Clears the entire display.
 */
function clearDisplay() {
    display.value = '';
}

/**
 * Deletes the last character from the display.
 */
function deleteLast() {
    display.value = display.value.slice(0, -1);
}

/**
 * Sends the current expression to the backend for evaluation.
 * Updates the display with the result and refreshes the history.
 */
async function calculate() {
    const expression = display.value;
    if (!expression) return;

    try {
        const response = await fetch('calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ expression: expression })
        });

        const data = await response.json();
        
        if (data.result !== undefined) {
            display.value = data.result;
            loadHistory(); // Refresh history panel
        } else if (data.error) {
            alert(data.error);
        }
    } catch (error) {
        console.error('Calculation Error:', error);
        alert('Serverfehler bei der Berechnung.');
    }
}

/**
 * Fetches the calculation history from the backend and renders it.
 */
async function loadHistory() {
    try {
        const response = await fetch('history');
        const historyData = await response.json();

        historyList.innerHTML = ''; // Clear current list

        if (historyData.length === 0) {
            historyList.innerHTML = '<p class="empty-msg">Noch keine Berechnungen.</p>';
            return;
        }

        historyData.forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-item';
            div.innerHTML = `
                <span class="expr">${item.expression}</span>
                <span class="res">= ${item.result}</span>
            `;
            // Clicking history item restores the expression to the display
            div.onclick = () => {
                display.value = item.expression;
            };
            historyList.appendChild(div);
        });
    } catch (error) {
        console.error('History Error:', error);
    }
}

/**
 * Requests the backend to clear the calculation history.
 */
async function clearHistory() {
    if (!confirm('Verlauf wirklich löschen?')) return;

    try {
        await fetch('clear_history', { method: 'POST' });
        loadHistory();
    } catch (error) {
        console.error('Clear History Error:', error);
    }
}

/**
 * Toggles between Light and Dark mode.
 */
function toggleTheme() {
    const body = document.body;
    if (body.classList.contains('light-mode')) {
        body.classList.replace('light-mode', 'dark-mode');
        themeIcon.textContent = '☀️';
        localStorage.setItem('theme', 'dark');
    } else {
        body.classList.replace('dark-mode', 'light-mode');
        themeIcon.textContent = '🌙';
        localStorage.setItem('theme', 'light');
    }
}

// -----------------------------------------------------------------------------
// Event Listeners & Initialization
// -----------------------------------------------------------------------------

// Theme Toggle Listener
themeToggle.onclick = toggleTheme;

// Keyboard Support
document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') calculate();
    else if (e.key === 'Backspace') deleteLast();
    else if (e.key === 'Escape') clearDisplay();
    // Support numeric and operator keys
    else if ("0123456789+-*/().%^".includes(e.key)) {
        append(e.key);
    }
});

// Initialize on Load
window.onload = () => {
    // Restore theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.replace('light-mode', 'dark-mode');
        themeIcon.textContent = '☀️';
    }
    
    loadHistory(); // Load initial history
};
