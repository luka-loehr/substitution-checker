class Dashboard {
    constructor() {
        this.userData = null;
        this.checkAuthentication();
        this.loadUserData();
        this.initializeEventListeners();
    }

    checkAuthentication() {
        if (!localStorage.getItem('userData')) {
            window.location.href = 'index.html';
        }
    }

    loadUserData() {
        this.userData = JSON.parse(localStorage.getItem('userData'));
        this.updateWelcomeMessage();
        this.updateSettingsForm();
    }

    updateWelcomeMessage() {
        document.getElementById('welcomeMessage').textContent = `Willkommen, ${this.userData.name}`;
        document.getElementById('userClass').textContent = `Klasse ${this.userData.class}`;
    }

    updateSettingsForm() {
        document.getElementById('emailSetting').value = this.userData.email;
        document.getElementById('timeSetting').value = this.userData.notificationTime;
    }

    initializeEventListeners() {
        document.getElementById('checkButton')?.addEventListener('click', () => this.checkSubstitutions());
    }

    async checkSubstitutions() {
        const button = document.getElementById('checkButton');
        
        try {
            button.textContent = 'Überprüfe Vertretungen';
            button.classList.add('loading-dots');
            button.disabled = true;

            const response = await this.triggerGitHubWorkflow();

            if (response.status === 204) {
                this.showSuccess(button);
            } else {
                throw new Error('Workflow trigger failed');
            }
        } catch (error) {
            this.showError(button);
        }
    }

    async triggerGitHubWorkflow() {
        return await fetch(
            'https://api.github.com/repos/luka-loehr/substitution-checker/actions/workflows/check-substitutions.yml/dispatches',
            {
                method: 'POST',
                headers: {
                    'Authorization': `token ${localStorage.getItem('github_token')}`,
                    'Accept': 'application/vnd.github.v3+json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ ref: 'main' })
            }
        );
    }

    showSuccess(button) {
        button.classList.remove('loading-dots');
        button.classList.add('success');
        button.textContent = 'Keine Vertretungen für Montag';
        
        setTimeout(() => this.resetButton(button), 10000);
    }

    showError(button) {
        button.classList.remove('loading-dots');
        button.classList.add('error');
        button.textContent = 'Fehler bei der Überprüfung';
        
        setTimeout(() => this.resetButton(button), 5000);
    }

    resetButton(button) {
        button.classList.remove('success', 'error');
        button.textContent = 'Nach Vertretungen suchen';
        button.disabled = false;
    }
}

// Initialize Dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => new Dashboard());
