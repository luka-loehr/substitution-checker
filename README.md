# Substitute Teacher Checker

This program automatically checks for substitute teacher information for class 9b from your school's website, and sends an email with the results. It's set up to run in the cloud using GitHub Actions.

## How It Works

1. The program downloads the substitute teacher schedule PDF from the school website
2. It extracts text from the PDF
3. It uses OpenAI to analyze the content and check for class 9b substitutions
4. It emails the results in a nicely formatted message to the specified recipient
5. It runs automatically at 7 PM German time every day

## Setup Guide

### GitHub Repository Setup

1. Create a GitHub repository (private recommended)
2. Upload the following files:
   - `main.py` - The main script
   - `requirements.txt` - Python package requirements
   - `.github/workflows/check-substitutions.yml` - GitHub Actions workflow file
   - `README.md` - This readme file

### Adding Required Secrets

Add these secrets to your GitHub repository:
1. Go to your repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each of these required secrets:

| Secret Name | Description |
|-------------|-------------|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `EMAIL_USERNAME` | Your Gmail address |
| `EMAIL_PASSWORD` | Your Google app password |
| `RECIPIENT_EMAIL` | The email address to send results to |
| `AUTH_USERNAME` | Username for the school website |
| `AUTH_PASSWORD` | Password for the school website |
| `PDF_URL` | URL of the PDF |

### Gmail Setup for App Passwords

1. Go to your [Google Account settings](https://myaccount.google.com/)
2. Click on "Security" in the left sidebar
3. Enable "2-Step Verification" if not already enabled
4. Go back to the Security page
5. Scroll down to find "App passwords"
6. Create a new app password:
   - Select "Mail" as the app
   - Select "Other" as the device (name it "SubstituteChecker")
   - Click "Generate"
7. Copy the 16-character password Google gives you
8. Use this password for the `EMAIL_PASSWORD` secret

## Running the Program

The program will run automatically according to the GitHub Actions workflow schedule (daily at 7 PM German time).

To run it manually:
1. Go to the "Actions" tab in your repository
2. Select the "Check Substitutions" workflow
3. Click "Run workflow" → "Run workflow"

## Local Development

To run the program locally:

1. Clone the repository
2. Create a `.env` file with all the required variables (use the template below)
3. Install the required packages: `pip install -r requirements.txt`
4. Run the script: `python main.py`

Example `.env` file:
```
# OpenAI API key
OPENAI_API_KEY=

# Email settings
EMAIL_USERNAME=
EMAIL_PASSWORD=
RECIPIENT_EMAIL=

# School website
AUTH_USERNAME=
AUTH_PASSWORD=
PDF_URL=
```

## Troubleshooting

Check the GitHub Actions logs for any errors:
1. Go to the "Actions" tab
2. Click on the most recent workflow run
3. Click on the "check" job
4. Expand the "Run script" step to see the detailed logs

Common issues:
- OpenAI API key invalid or expired
- Email authentication failed (check your app password)
- PDF could not be downloaded (check URL and credentials)

## Customizing the Program

- To change the time when the check runs, modify the cron expressions in `.github/workflows/check-substitutions.yml`
- To change the class being checked or the message format, modify the prompt in `analyze_with_openai()` function in `main.py`
