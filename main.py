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

# Set up logging with more detailed format
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
        
        logging.info("Successfully extracted text from PDF (%d characters)", len(text))
        return text
    except Exception as e:
        logging.error("Failed to extract text from PDF: %s", str(e))
        return f"Error extracting text: {str(e)}"

def download_pdf():
    """Download the PDF from the URL with authentication."""
    url = os.getenv("PDF_URL")
    auth_username = os.getenv("AUTH_USERNAME")
    auth_password = os.getenv("AUTH_PASSWORD")
    
    if not url:
        logging.error("PDF_URL not found in environment variables")
        return None
    
    if not auth_username or not auth_password:
        logging.error("Authentication credentials not found in environment variables")
        return None
    
    logging.info("Attempting to download PDF from %s", url)
    
    try:
        response = requests.get(url, auth=(auth_username, auth_password))
        
        if response.status_code == 200:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.write(response.content)
            temp_file_path = temp_file.name
            temp_file.close()
            
            logging.info("PDF downloaded successfully to %s", temp_file_path)
            return temp_file_path
        else:
            logging.error("Failed to download PDF. Status code: %s, Response: %s", 
                         response.status_code, response.text[:200])
            return None
    except Exception as e:
        logging.error("Exception while downloading PDF: %s", str(e))
        return None

def send_email(analysis_result):
    """Send the analysis results via email."""
    recipient_email = os.getenv("RECIPIENT_EMAIL")
    if not recipient_email:
        logging.error("RECIPIENT_EMAIL not found in environment variables")
        return False
        
    logging.info("Preparing to send email to %s", recipient_email)
    
    email_username = os.getenv("EMAIL_USERNAME")
    email_password = os.getenv("EMAIL_PASSWORD")
    
    if not email_username or not email_password:
        logging.error("Email credentials not found in environment variables")
        return False
    
    logging.info("Email configuration:")
    logging.info("- Using username: %s", email_username)
    logging.info("- Password length: %d characters", len(email_password))
    logging.info("- To: %s", recipient_email)
    logging.info("- Content length: %d characters", len(analysis_result))
    
    # Create the email
    msg = MIMEMultipart()
    msg['From'] = email_username
    msg['To'] = recipient_email
    msg['Subject'] = "Vertretungen für Montag"  # This will be overridden by the actual day
    msg.attach(MIMEText(analysis_result, 'plain'))
    
    try:
        logging.info("Connecting to SMTP server (smtp.gmail.com:587)...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.set_debuglevel(1)  # Enable SMTP debug logging
        
        logging.info("Starting TLS connection...")
        server.starttls()
        
        logging.info("Attempting login...")
        server.login(email_username, email_password)
        
        logging.info("Sending email...")
        server.send_message(msg)
        
        logging.info("Closing SMTP connection...")
        server.quit()
        
        logging.info("Email sent successfully")
        return True
    except smtplib.SMTPAuthenticationError as e:
        logging.error("SMTP Authentication failed: %s", str(e))
        return False
    except smtplib.SMTPException as e:
        logging.error("SMTP error occurred: %s", str(e))
        return False
    except Exception as e:
        logging.error("Unexpected error during email sending: %s", str(e))
        return False

def analyze_with_openai(pdf_path):
    """Analyze the PDF using OpenAI API."""
    logging.info("Starting OpenAI analysis...")
    
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logging.error("OPENAI_API_KEY not found in environment variables")
            return "Error: OpenAI API key not configured"
        
        pdf_text = extract_text_from_pdf(pdf_path)
        if pdf_text.startswith("Error"):
            return pdf_text
        
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
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher Assistent, der Vertretungspläne für Schüler analysiert und die Informationen präzise nach den angegebenen Formulierungsregeln aufbereitet."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        if response.choices and len(response.choices) > 0:
            result = response.choices[0].message.content
            logging.info("Analysis result: %s", result)
            return result
        
        logging.warning("No response content found")
        return "No analysis results found."
    except Exception as e:
        logging.error("Exception during OpenAI analysis: %s", str(e))
        return f"Error during analysis: {str(e)}"

def cleanup(pdf_path):
    """Clean up temporary files."""
    if pdf_path and os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
            logging.info("Temporary file %s removed", pdf_path)
        except Exception as e:
            logging.error("Failed to remove temporary file: %s", str(e))

def check_env_variables():
    """Check if all required environment variables are set."""
    required_vars = ["OPENAI_API_KEY", "EMAIL_USERNAME", "EMAIL_PASSWORD", "RECIPIENT_EMAIL", 
                     "AUTH_USERNAME", "AUTH_PASSWORD", "PDF_URL"]
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # Log the length of the value for debugging (don't log actual values)
            logging.info("Found %s with length: %d", var, len(value))
    
    if missing_vars:
        logging.error("Missing required environment variables: %s", ", ".join(missing_vars))
        return False
    
    logging.info("All required environment variables are set")
    return True

def main():
    """Main function to orchestrate the process."""
    logging.info("=== Starting Substitute Teacher Checker ===")
    logging.info("Running in environment: %s", "GitHub Actions" if os.getenv("GITHUB_ACTIONS") else "Local")
    
    if not check_env_variables():
        return
    
    pdf_path = download_pdf()
    
    if not pdf_path:
        logging.error("Exiting due to PDF download failure")
        return
    
    try:
        logging.info("Starting OpenAI analysis...")
        analysis_result = analyze_with_openai(pdf_path)
        logging.info("Analysis result: %s", analysis_result)
        
        logging.info("Sending email with analysis results...")
        email_sent = send_email(analysis_result)
        
        if email_sent:
            logging.info("Process completed successfully")
        else:
            logging.error("Process completed with errors (email not sent)")
    except Exception as e:
        logging.error("Unexpected error in main process: %s", str(e))
    finally:
        cleanup(pdf_path)
        logging.info("=== Substitute Teacher Checker Finished ===")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical("Critical error: %s", str(e))
        print(f"Critical error occurred. Check app.log for details.")
