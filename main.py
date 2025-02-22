import requests
import tempfile
import os
import smtplib
import logging
import time
import pytz
import re
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import PyPDF2
from openai import OpenAI
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def is_evening_in_germany():
    """Check if it's currently between 6:45 PM and 7:15 PM in Germany."""
    germany_tz = pytz.timezone('Europe/Berlin')
    current_time = datetime.now(germany_tz)
    # Only run if it's between 6:45 PM and 7:15 PM in Germany
    return 18.75 <= current_time.hour + (current_time.minute / 60) <= 19.25

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    logging.info("Extracting text from PDF: %s", pdf_path)
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n\n"
        
        logging.info("Successfully extracted %d characters from PDF", len(text))
        return text
    except Exception as e:
        logging.error("Failed to extract text from PDF: %s", str(e))
        return f"Error extracting text: {str(e)}"

def download_pdf():
    """Download the PDF from the URL with authentication."""
    # Get URL and authentication details from environment variables
    url = os.getenv("PDF_URL")
    auth_username = os.getenv("AUTH_USERNAME")
    auth_password = os.getenv("AUTH_PASSWORD")
    
    if not url:
        logging.error("PDF_URL not found in environment variables")
        return None
    
    if not auth_username or not auth_password:
        logging.error("Authentication credentials not found in environment variables")
        return None
    
    logging.info("Downloading PDF from %s", url)
    
    try:
        response = requests.get(url, auth=(auth_username, auth_password))
        
        if response.status_code == 200:
            # Create a temporary file to store the PDF
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.write(response.content)
            temp_file_path = temp_file.name
            temp_file.close()
            
            logging.info("PDF downloaded successfully to %s", temp_file_path)
            return temp_file_path
        else:
            logging.error("Failed to download PDF. Status code: %s", response.status_code)
            return None
    except Exception as e:
        logging.error("Exception while downloading PDF: %s", str(e))
        return None

def extract_day_from_text(text, analysis_result):
    """Extract the day of week from either the PDF text or the analysis result."""
    # First try to find weekday names directly
    german_weekdays = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
    
    # Look for weekday in analysis result first (more likely to be formatted clearly)
    # Check for the new format first
    match = re.search(r'Für (\w+)', analysis_result)
    if match:
        return match.group(1)
        
    # Check for old format as fallback
    match = re.search(r'Hallo Luka, für (\w+)', analysis_result)
    if match:
        return match.group(1)
    
    # Then look in the PDF text
    for day in german_weekdays:
        if day in text:
            return day
    
    # If no weekday found directly, try to extract a date and convert it to weekday
    date_patterns = [
        r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # 25.02.2025
        r'(\d{1,2})\.(\d{1,2})\.',       # 25.02.
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        if matches:
            try:
                # If we have a full date with year
                if len(matches[0]) == 3:
                    day, month, year = matches[0]
                    date_obj = datetime(int(year), int(month), int(day))
                # If we only have day and month
                else:
                    day, month = matches[0]
                    current_year = datetime.now().year
                    date_obj = datetime(current_year, int(month), int(day))
                
                # Get the weekday name in German
                weekday_index = date_obj.weekday()  # 0 = Monday, 6 = Sunday
                return german_weekdays[weekday_index]
            except (ValueError, IndexError):
                pass
    
    # Fallback to current day of week if nothing found
    germany_tz = pytz.timezone('Europe/Berlin')
    current_time = datetime.now(germany_tz)
    weekday_index = current_time.weekday()
    return german_weekdays[weekday_index]

def analyze_with_openai(pdf_path):
    """Analyze the PDF using OpenAI API."""
    logging.info("Starting analysis with OpenAI...")
    
    try:
        # Check if API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            logging.error("OPENAI_API_KEY not found in environment variables")
            return "Error: OpenAI API key not configured"
        
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(pdf_path)
        if pdf_text.startswith("Error"):
            return pdf_text
        
        # The prompt to analyze the substitute teacher information with detailed instructions
        instruction = """
        Bitte schaue ob es vertretungen für die klasse 9b gibt.
        
        Formatiere die Antwort mit folgenden Kriterien:
        
        1. Beginne immer mit "Für [Wochentag]..." - WICHTIG: Nenne NUR den Wochentag (Montag, Dienstag, usw.), KEIN Datum.
        
        2. Wenn es keine Vertretungen gibt, schreibe:
           "Für [Wochentag] gibt es keine Vertretungen für die Klasse 9b."
        
        3. Wenn es Vertretungen gibt, schreibe:
           "Für [Wochentag] gibt es folgende Vertretungen: [Vertretungen]"
        
        4. Bei Änderungen beachte folgende Regeln:
           - Wenn es die ersten beiden Stunden sind, sage "in den ersten beiden Stunden"
           - Bei 3. und 4. Stunde sage "in der dritten und vierten Stunde"
           - Bei 5. und 6. Stunde sage "in der fünften und sechsten Stunde"
           - Bei Nachmittagsunterricht:
             * Wenn der gesamte Nachmittagsunterricht ausfällt, sage nur "der Nachmittagsunterricht fällt aus" ohne weitere Angaben
             * Wenn nur ein Fach des Nachmittagsunterrichts ausfällt, gib das genau an
        
        5. Bei Verlegungen:
           - Sage welches Fach ausgefallen ist
           - In welchen Stunden es jetzt Vertretung gibt
           - In welchem Fach die Vertretung stattfindet
           - Bei welchem Lehrer
        
        WICHTIG: Verwende NUR den Wochentag, niemals das Datum. Also "Für Montag..." statt "Für Montag den 24. Februar..."
        
        Benutze die genauen Details aus dem Vertretungsplan.
        """
        
        prompt = f"{instruction}\n\nHier ist der Inhalt des Vertretungsplans:\n\n{pdf_text}"
        
        logging.info("Sending request to OpenAI Chat API...")
        
        # Use the chat completions API instead of assistants API
        response = client.chat.completions.create(
            model="gpt-4o",  # or another appropriate model
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher Assistent, der Vertretungspläne für Schüler analysiert und die Informationen präzise nach den angegebenen Formulierungsregeln aufbereitet."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        if response.choices and len(response.choices) > 0:
            result = response.choices[0].message.content
            logging.info("Analysis result retrieved successfully")
            return result
        
        logging.warning("No response content found")
        return "No analysis results found."
    except Exception as e:
        logging.error("Exception during OpenAI analysis: %s", str(e))
        return f"Error during analysis: {str(e)}"

def send_email(analysis_result, pdf_text=""):
    """Send the analysis results via email."""
    # Get recipient email from environment variables
    recipient_email = os.getenv("RECIPIENT_EMAIL")
    
    if not recipient_email:
        logging.error("RECIPIENT_EMAIL not found in environment variables")
        return False
    
    # Extract day from text for email subject
    day = extract_day_from_text(pdf_text, analysis_result)
    subject = f"Vertretungen für {day}"
    logging.info("Email subject: %s", subject)
        
    logging.info("Preparing to send email to %s", recipient_email)
    
    # Use environment variables for email authentication
    email_username = os.getenv("EMAIL_USERNAME")
    email_password = os.getenv("EMAIL_PASSWORD")
    
    if not email_username or not email_password:
        logging.error("Email credentials not found in .env file")
        return False
    
    # Create the email
    msg = MIMEMultipart()
    msg['From'] = email_username
    msg['To'] = recipient_email
    msg['Subject'] = subject
    
    # Attach the analysis result
    msg.attach(MIMEText(analysis_result, 'plain'))
    
    try:
        # Connect to the SMTP server
        logging.info("Connecting to SMTP server...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        # Login with your credentials
        logging.info("Logging in to email account...")
        server.login(email_username, email_password)
        
        # Send the email
        logging.info("Sending email...")
        server.send_message(msg)
        
        # Close the connection
        server.quit()
        
        logging.info("Email sent successfully to %s", recipient_email)
        return True
    except Exception as e:
        logging.error("Failed to send email: %s", str(e))
        return False

def cleanup(pdf_path):
    """Clean up temporary files."""
    if pdf_path and os.path.exists(pdf_path):
        os.remove(pdf_path)
        logging.info("Temporary file %s removed", pdf_path)

def check_env_variables():
    """Check if all required environment variables are set."""
    required_vars = ["OPENAI_API_KEY", "EMAIL_USERNAME", "EMAIL_PASSWORD", "RECIPIENT_EMAIL", 
                     "AUTH_USERNAME", "AUTH_PASSWORD", "PDF_URL"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logging.error("Missing required environment variables: %s", ", ".join(missing_vars))
        logging.error("Please check your .env file and make sure all required variables are set")
        return False
    
    logging.info("All required environment variables are set")
    return True

def main():
    """Main function to orchestrate the process."""
    logging.info("=== Starting Substitute Teacher Checker ===")
    
    # When running in GitHub Actions, check if it's evening in Germany
    if os.getenv("GITHUB_ACTIONS") == "true":
        if not is_evening_in_germany():
            logging.info("Not running - it's not evening in Germany right now")
            return
    
    # Check environment variables
    if not check_env_variables():
        return
    
    # Download the PDF
    pdf_path = download_pdf()
    
    if not pdf_path:
        logging.error("Exiting due to PDF download failure")
        return
    
    try:
        # Extract text from PDF for later use
        pdf_text = extract_text_from_pdf(pdf_path)
        
        # Analyze the PDF with OpenAI
        logging.info("Starting OpenAI analysis...")
        analysis_result = analyze_with_openai(pdf_path)
        logging.info("Analysis result: %s", analysis_result)
        
        # Send the email with the results
        logging.info("Sending email with analysis results...")
        email_sent = send_email(analysis_result, pdf_text)
        
        if email_sent:
            logging.info("Process completed successfully")
        else:
            logging.error("Process completed with errors (email not sent)")
    except Exception as e:
        logging.error("Unexpected error in main process: %s", str(e))
    finally:
        # Clean up temporary files
        cleanup(pdf_path)
        logging.info("=== Substitute Teacher Checker Finished ===")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical("Critical error: %s", str(e))
        print(f"Critical error occurred. Check app.log for details.")
