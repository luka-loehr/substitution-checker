import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";
import { getDatabase, ref, get, set } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-database.js";

// Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyBy228bRkP0vgDG6DFPy5etBxThb2Ene0s",
    authDomain: "vertretungsplan-checker.firebaseapp.com",
    projectId: "vertretungsplan-checker",
    storageBucket: "vertretungsplan-checker.firebasestorage.app",
    messagingSenderId: "98128959337",
    appId: "1:98128959337:web:85dbc6d6c4fa1f95924ff8"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const database = getDatabase(app);

class Dashboard {
    constructor() {
        this.userData = null;
        this.checkAuthentication();
        this.initializeEventListeners();
    }

    async checkAuthentication() {
        auth.onAuthStateChanged(async (user) => {
            if (user) {
                await this.loadUserData(user.uid);
            } else {
                window.location.href = 'index.html';
            }
        });
    }

    async loadUserData(userId) {
        try {
            const snapshot = await get(ref(database, 'users/' + userId));
            this.userData = snapshot.val();
            this.updateUI();
        } catch (error) {
            console.error('Error loading user data:', error);
            alert('Fehler beim Laden der Benutzerdaten');
        }
    }

    updateUI() {
        // Update welcome message
        document.getElementById('welcomeMessage').textContent = `Willkommen, ${this.userData.name}`;
        document.getElementById('userClass').textContent = `Klasse ${this.userData.class}`;

        // Update settings form
        document.getElementById('emailSetting').value = this.userData.email;
        document.getElementById('timeSetting').value = this.userData.notificationTime || "19:00";
    }

    initializeEventListeners() {
        document.getElementById('checkButton')?.addEventListener('click', () => this.checkSubstitutions());
        document.querySelector('.settings-icon')?.addEventListener('click', () => this.toggleSettings());
        document.getElementById('saveSettings')?.addEventListener('click', () => this.saveSettings());
        document.getElementById('logoutButton')?.addEventListener('click', () => this.logout());
    }

    async checkSubstitutions() {
        const button = document.getElementById('checkButton');
        
        try {
            this.setButtonLoading(button);
            
            // Simulate checking for substitutions (replace with actual check later)
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Random result for demonstration
            const hasSubstitutions = Math.random() > 0.5;
            
            if (hasSubstitutions) {
                this.setButtonSuccess(button, "Für Montag hast du in der dritten und vierten Stunde Sport statt Mathe");
            } else {
                this.setButtonError(button, "Keine Vertretungen für Montag");
            }
            
            // Reset button after 10 seconds
            setTimeout(() => this.resetButton(button), 10000);
            
        } catch (error) {
            this.setButtonError(button, "Fehler bei der Überprüfung");
            setTimeout(() => this.resetButton(button), 5000);
        }
    }

    setButtonLoading(button) {
        button.textContent = "Überprüfe Vertretungen";
        button.classList.add('loading-dots');
        button.disabled = true;
    }

    setButtonSuccess(button, text) {
        button.classList.remove('loading-dots');
        button.classList.add('success');
        button.textContent = text;
        button.style.whiteSpace = 'normal';
        button.style.height = 'auto';
        button.style.minHeight = '4rem';
    }

    setButtonError(button, text) {
        button.classList.remove('loading-dots');
        button.classList.add('error');
        button.textContent = text;
    }

    resetButton(button) {
        button.classList.remove('success', 'error');
        button.textContent = 'Nach Vertretungen suchen';
        button.disabled = false;
        button.style.whiteSpace = '';
        button.style.height = '';
        button.style.minHeight = '';
    }

    toggleSettings() {
        const panel = document.getElementById('settingsPanel');
        panel.classList.toggle('active');
    }

    async saveSettings() {
        try {
            const newEmail = document.getElementById('emailSetting').value;
            const newTime = document.getElementById('timeSetting').value;

            // Update database
            await set(ref(database, `users/${auth.currentUser.uid}/email`), newEmail);
            await set(ref(database, `users/${auth.currentUser.uid}/notificationTime`), newTime);

            this.userData.email = newEmail;
            this.userData.notificationTime = newTime;

            alert('Einstellungen gespeichert!');
            this.toggleSettings();
        } catch (error) {
            console.error('Error saving settings:', error);
            alert('Fehler beim Speichern der Einstellungen');
        }
    }

    async logout() {
        try {
            await auth.signOut();
            window.location.href = 'index.html';
        } catch (error) {
            console.error('Error logging out:', error);
            alert('Fehler beim Ausloggen');
        }
    }
}

// Initialize Dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => new Dashboard());
