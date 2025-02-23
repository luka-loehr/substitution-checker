class Setup {
    constructor() {
        this.checkExistingUser();
        this.initializeEventListeners();
    }

    checkExistingUser() {
        if (localStorage.getItem('userData')) {
            window.location.href = 'dashboard.html';
        }
    }

    initializeEventListeners() {
        document.getElementById('nextButton')?.addEventListener('click', () => this.nextStep());
        document.getElementById('finishButton')?.addEventListener('click', () => this.finishSetup());
    }

    nextStep() {
        const name = document.getElementById('userName').value.trim();
        const className = document.getElementById('userClass').value.trim();

        if (!this.validateInputs(name, className)) {
            return;
        }

        document.getElementById('step1').classList.add('hidden');
        document.getElementById('step2').classList.remove('hidden');
    }

    validateInputs(...inputs) {
        for (const input of inputs) {
            if (!input) {
                this.showError('Bitte fülle alle Felder aus.');
                return false;
            }
        }
        return true;
    }

    showError(message) {
        // Implementiere hier deine Fehleranzeige
        alert(message);
    }

    finishSetup() {
        const userData = {
            name: document.getElementById('userName').value.trim(),
            class: document.getElementById('userClass').value.trim(),
            email: document.getElementById('userEmail').value.trim(),
            notificationTime: document.getElementById('notificationTime').value,
            settings: {
                emailNotifications: true
            }
        };

        if (!this.validateInputs(userData.name, userData.class, userData.email, userData.notificationTime)) {
            return;
        }

        localStorage.setItem('userData', JSON.stringify(userData));
        window.location.href = 'dashboard.html';
    }
}

// Initialize Setup when DOM is loaded
document.addEventListener('DOMContentLoaded', () => new Setup());
