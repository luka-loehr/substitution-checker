import { getAuth } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";
import { getDatabase, ref, set } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-database.js";

class Settings {
    constructor() {
        this.auth = getAuth();
        this.database = getDatabase();
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Settings toggle
        document.querySelector('.settings-icon')?.addEventListener('click', () => this.toggleSettings());
        
        // Save settings
        document.getElementById('saveSettings')?.addEventListener('click', () => this.saveSettings());
        
        // Email notification toggle
        document.getElementById('emailToggle')?.addEventListener('change', (e) => this.toggleEmailNotifications(e.target.checked));
        
        // Theme toggle (if you want to add dark/light mode)
        document.getElementById('themeToggle')?.addEventListener('change', (e) => this.toggleTheme(e.target.checked));
    }

    toggleSettings() {
        const panel = document.getElementById('settingsPanel');
        if (panel.classList.contains('active')) {
            // Animate out
            panel.style.transform = 'translateY(20px)';
            panel.style.opacity = '0';
            setTimeout(() => {
                panel.classList.remove('active');
                panel.style.transform = '';
                panel.style.opacity = '';
            }, 300);
        } else {
            // Animate in
            panel.classList.add('active');
            panel.style.transform = 'translateY(0)';
            panel.style.opacity = '1';
        }
    }

    async saveSettings() {
        try {
            const userId = this.auth.currentUser.uid;
            const newSettings = {
                email: document.getElementById('emailSetting').value,
                notificationTime: document.getElementById('timeSetting').value,
                emailNotifications: document.getElementById('emailToggle').checked,
                theme: document.getElementById('themeToggle')?.checked ? 'dark' : 'light'
            };

            // Validate email
            if (!this.validateEmail(newSettings.email)) {
                throw new Error('Ungültige E-Mail-Adresse');
            }

            // Save to Firebase
            await set(ref(this.database, `users/${userId}/settings`), newSettings);

            // Show success animation
            this.showSuccessMessage();
            
            // Close settings panel after delay
            setTimeout(() => this.toggleSettings(), 1500);

        } catch (error) {
            this.showErrorMessage(error.message);
        }
    }

    validateEmail(email) {
        return email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/);
    }

    async toggleEmailNotifications(enabled) {
        try {
            const userId = this.auth.currentUser.uid;
            await set(ref(this.database, `users/${userId}/settings/emailNotifications`), enabled);
            this.showSuccessMessage(`E-Mail-Benachrichtigungen ${enabled ? 'aktiviert' : 'deaktiviert'}`);
        } catch (error) {
            this.showErrorMessage('Fehler beim Ändern der Benachrichtigungseinstellungen');
        }
    }

    toggleTheme(isDark) {
        document.body.classList.toggle('dark-theme', isDark);
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    }

    showSuccessMessage(message = 'Einstellungen gespeichert!') {
        const toast = document.createElement('div');
        toast.className = 'success-toast';
        toast.textContent = message;
        document.body.appendChild(toast);

        // Animate in
        setTimeout(() => toast.classList.add('show'), 100);

        // Remove after delay
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    showErrorMessage(message) {
        const toast = document.createElement('div');
        toast.className = 'error-toast';
        toast.textContent = message;
        document.body.appendChild(toast);

        // Animate in
        setTimeout(() => toast.classList.add('show'), 100);

        // Remove after delay
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Method to load user settings
    async loadUserSettings() {
        try {
            const userId = this.auth.currentUser.uid;
            const settingsRef = ref(this.database, `users/${userId}/settings`);
            const snapshot = await get(settingsRef);
            
            if (snapshot.exists()) {
                const settings = snapshot.val();
                this.applySettings(settings);
            }
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }

    // Apply loaded settings to UI
    applySettings(settings) {
        if (settings.email) {
            document.getElementById('emailSetting').value = settings.email;
        }
        if (settings.notificationTime) {
            document.getElementById('timeSetting').value = settings.notificationTime;
        }
        if (typeof settings.emailNotifications !== 'undefined') {
            document.getElementById('emailToggle').checked = settings.emailNotifications;
        }
        if (settings.theme) {
            const isDark = settings.theme === 'dark';
            document.getElementById('themeToggle').checked = isDark;
            this.toggleTheme(isDark);
        }
    }
}

// Initialize Settings when DOM is loaded
document.addEventListener('DOMContentLoaded', () => new Settings());
