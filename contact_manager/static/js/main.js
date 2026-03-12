document.addEventListener('DOMContentLoaded', () => {
    const contactForm = document.getElementById('contact-form');
    const contactResults = document.getElementById('contact-results');
    const searchInput = document.getElementById('search-input');
    const submitBtn = document.getElementById('submit-btn');
    const resetBtn = document.getElementById('reset-btn');
    const deleteBtn = document.getElementById('delete-btn');
    const contactIndexInput = document.getElementById('contact-index');
    const themeToggle = document.getElementById('theme-toggle');
    const showAllBtn = document.getElementById('show-all-btn');
    const listSection = document.getElementById('list-section');

    let allContacts = [];
    let isEditing = false;
    let selectedContactIndex = -1;

    // Fetch and display contacts (internal state update)
    async function loadContacts() {
        try {
            // Using absolute paths relative to the current site (which starts with /contact-manager)
            const response = await fetch('/contact-manager/api/contacts');
            allContacts = await response.json();
        } catch (error) {
            console.error('Fehler beim Laden:', error);
        }
    }

    function renderResults(contacts) {
        if (contacts.length === 0) {
            listSection.classList.add('hidden');
            return;
        }

        listSection.classList.remove('hidden');
        contactResults.innerHTML = '';
        contacts.forEach((contact, index) => {
            const actualIndex = allContacts.indexOf(contact);
            
            const card = document.createElement('div');
            card.className = `contact-card ${selectedContactIndex === actualIndex ? 'active' : ''}`;
            
            const initials = (contact.vorname?.[0] || '') + (contact.nachname?.[0] || '');
            
            card.innerHTML = `
                <div class="initials">${initials.toUpperCase()}</div>
                <h3>${contact.vorname || ''} ${contact.nachname || ''}</h3>
            `;
            
            card.addEventListener('click', () => selectContact(actualIndex));
            contactResults.appendChild(card);
        });
    }

    function selectContact(index) {
        const contact = allContacts[index];
        selectedContactIndex = index;
        
        document.getElementById('vorname').value = contact.vorname || '';
        document.getElementById('nachname').value = contact.nachname || '';
        document.getElementById('strasse').value = contact.strasse || '';
        document.getElementById('plz').value = contact.plz || '';
        document.getElementById('email').value = contact.email || '';
        document.getElementById('rufnummer').value = contact.rufnummer || '';
        document.getElementById('mobil').value = contact.mobil || '';
        
        contactIndexInput.value = index;
        isEditing = true;
        
        submitBtn.textContent = 'Aktualisieren';
        deleteBtn.classList.remove('hidden');
        
        const cards = document.querySelectorAll('.contact-card');
        cards.forEach((c, i) => {
            c.classList.toggle('active', allContacts.indexOf(allContacts[i]) === index);
        });

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    contactForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const data = {
            vorname: document.getElementById('vorname').value.trim(),
            nachname: document.getElementById('nachname').value.trim(),
            strasse: document.getElementById('strasse').value.trim(),
            plz: document.getElementById('plz').value.trim(),
            email: document.getElementById('email').value.trim(),
            rufnummer: document.getElementById('rufnummer').value.trim(),
            mobil: document.getElementById('mobil').value.trim()
        };

        try {
            let url = '/contact-manager/api/contacts';
            let method = 'POST';

            if (isEditing) {
                url = `/contact-manager/api/contacts/${selectedContactIndex}`;
                method = 'PUT';
            }

            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                await loadContacts();
                if (isEditing) {
                    triggerSearch();
                } else {
                    resetForm();
                    triggerSearch();
                }
            }
        } catch (error) {
            console.error('Fehler beim Speichern:', error);
        }
    });

    function triggerSearch() {
        const term = searchInput.value.toLowerCase().trim();
        if (term === '') {
            listSection.classList.add('hidden');
            return;
        }

        const filtered = allContacts.filter(c => 
            (c.vorname && c.vorname.toLowerCase().includes(term)) ||
            (c.nachname && c.nachname.toLowerCase().includes(term)) ||
            (c.rufnummer && c.rufnummer.includes(term)) ||
            (c.mobil && c.mobil.includes(term))
        );
        renderResults(filtered);
    }

    searchInput.addEventListener('input', triggerSearch);

    showAllBtn.addEventListener('click', () => {
        if (showAllBtn.textContent === 'Alle anzeigen') {
            renderResults(allContacts);
            searchInput.value = '';
            showAllBtn.textContent = 'Alle verbergen';
        } else {
            listSection.classList.add('hidden');
            showAllBtn.textContent = 'Alle anzeigen';
        }
    });

    searchInput.addEventListener('input', () => {
        if (searchInput.value.trim() !== '') {
            showAllBtn.textContent = 'Alle anzeigen';
        }
        triggerSearch();
    });

    const currentTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme);

    themeToggle.addEventListener('click', () => {
        let theme = document.documentElement.getAttribute('data-theme');
        let newTheme = theme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });

    async function deleteSelected() {
        if (selectedContactIndex === -1) return;
        
        if (confirm('Soll dieser Kontakt wirklich gelöscht werden?')) {
            try {
                const response = await fetch(`/contact-manager/api/contacts/${selectedContactIndex}`, { method: 'DELETE' });
                if (response.ok) {
                    resetForm();
                    await loadContacts();
                    triggerSearch();
                }
            } catch (error) {
                console.error('Fehler beim Löschen:', error);
            }
        }
    }

    deleteBtn.addEventListener('click', deleteSelected);

    function resetForm() {
        contactForm.reset();
        contactIndexInput.value = '';
        isEditing = false;
        selectedContactIndex = -1;
        submitBtn.textContent = 'Hinzufügen';
        deleteBtn.classList.add('hidden');
        
        document.querySelectorAll('.contact-card').forEach(c => c.classList.remove('active'));
    }

    resetBtn.addEventListener('click', resetForm);

    loadContacts();
});
