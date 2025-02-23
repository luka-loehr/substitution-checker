import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";
import { getDatabase, ref, set } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-database.js";

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

class Setup {
    constructor() {
        this.initializeEventListeners();
        this.checkExistingSession();
    }

    initializeEventListeners() {
        document.getElementById('registerButton')?.addEventListener('click', () => this.registerUser());
        document.getElementById('showLoginButton')?.addEventListener('click', () => this.showLoginModal());
        document.getElementById('loginButton')?.addEventListener('click', () => this.loginUser());
        document.getElementById('closeLoginModal')?.addEventListener('click', () => this.hideLoginModal());
    }

    async checkExistingSession() {
        auth.onAuthStateChanged((user) => {
            if (user) {
                window.location.href = 'dashboard.html';
            }
        });
    }

    showLoginModal() {
        document.getElementById('loginModal').classList.remove('hidden');
    }

    hideLoginModal() {
        document.getElementById('loginModal').classList.add('hidden');
    }

    async registerUser() {
        const name = document.getElementById('userName').value.trim();
        const className = document.getElementById('userClass').value.trim();
        const email = document.getElementById('userEmail').value.trim();

        if (!this.validateInputs(name, className, email)) {
            return;
        }

        try {
            // Create user with email and random password
            const password = this.generateRandomPassword();
            const userCredential = await createUserWithEmailAndPassword(auth, email, password);
            const user = userCredential.user;

            // Save additional user data
            await set(ref(database, 'users/' + user.uid), {
                name: name,
                class: className,
                email: email,
                notificationTime: "19:00",
                settings: {
                    emailNotifications: true
                }
            });

            // Store user data in localStorage for quick access
            localStorage.setItem('userName', name);
            localStorage.setItem('userClass', className);

            // Redirect to dashboard
            window.location.href = 'dashboard.html';
        } catch (error) {
            alert('Fehler bei der Registrierung: ' + error.message);
        }
    }

    async loginUser() {
        const email = document.getElementById('loginEmail').value;
        if (!email) {
            alert('Bitte gib deine E-Mail-Adresse ein.');
            return;
        }

        try {
            // For this application, we'll use a standard password since it's a simple school tool
            const standardPassword = "vertretungsplan2024";
            await signInWithEmailAndPassword(auth, email, standardPassword);
            window.location.href = 'dashboard.html';
        } catch (error) {
            alert('Login fehlgeschlagen: ' + error.message);
        }
    }

    validateInputs(...inputs) {
        for (const input of inputs) {
            if (!input) {
                alert('Bitte fülle alle Felder aus.');
                return false;
            }
        }
        return true;
    }

    generateRandomPassword() {
        // For this application, we'll use a standard password
        return "vertretungsplan2024";
    }
}

// Initialize Setup when DOM is loaded
document.addEventListener('DOMContentLoaded', () => new Setup());
