import requests
import tempfile
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import PyPDF2
from openai import OpenAI
from dotenv import load_dotenv

# Set up logging with detailed format to stdout for GitHub Actions
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    logging.info("PROGRESS: Extracting text from PDF...")
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n\n"
        logging.info("PROGRESS: Text extracted")
        return text
    except Exception as e:
        logging.error("ERROR: Failed to extract text from PDF: %s", str(e))
        return f"Error extracting text: {str(e)}"

def download_pdf():
    """Download the PDF from the URL with authentication."""
    url = os.getenv("PDF_URL")
    auth_username = os.getenv("AUTH_USERNAME")
    auth_password = os.getenv("AUTH_PASSWORD")
    
    logging.info("PROGRESS: Downloading PDF...")
    if not url or not auth_username or not auth_password:
        logging.error("ERROR: Missing PDF_URL or authentication credentials")
        return None
    
    try:
        response = requests.get(url, auth=(auth_username, auth_password))
        if response.status_code == 200:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.write(response.content)
            temp_file_path = temp_file.name
            temp_file.close()
            logging.info("PROGRESS: PDF downloaded successfully")
            return temp_file_path
        else:
            logging.error("ERROR: Failed to download PDF. Status code: %s", response.status_code)
            return None
    except Exception as e:
        logging.error("ERROR: Exception while downloading PDF: %s", str(e))
        return None

def send_email(analysis_result):
    """Send the analysis results via email."""
    recipient_email = os.getenv("RECIPIENT_EMAIL")
    email_username = os.getenv("EMAIL_USERNAME")
    email_password = os.getenv("EMAIL_PASSWORD")
    
    logging.info("PROGRESS: Sending email...")
    if not recipient_email or not email_username or not email_password:
        logging.error("ERROR: Missing email configuration")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = email_username
    msg['To'] = recipient_email
    msg['Subject'] = "Vertretungen Update"
    msg.attach(MIMEText(analysis_result, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_username, email_password)
        server.send_message(msg)
        server.quit()
        logging.info("PROGRESS: Email sent successfully")
        return True
    except Exception as e:
        logging.error("ERROR: Failed to send email: %s", str(e))
        return False

def analyze_with_openai(pdf_path):
    """Analyze the PDF using OpenAI API."""
    logging.info("PROGRESS: Analyzing with OpenAI...")
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logging.error("ERROR: OPENAI_API_KEY not found")
            return "Error: OpenAI API key not configured"
        
        pdf_text = extract_text_from_pdf(pdf_path)
        if pdf_text.startswith("Error"):
            return pdf_text
        
        instruction = """
        Bitte schaue ob es Vertretungen für die Klasse 9b gibt.
        
        Formatiere die Antwort mit folgenden Kriterien:
        
        1. Beginne immer mit "Für [Wochentag]..." - WICHTIG: NUR den Wochentag (Montag, Dienstag, usw.), KEIN Datum.
        2. Wenn es keine Vertretungen gibt, schreibe: "Für [Wochentag] gibt es keine Vertretungen für die Klasse 9b."
        3. Wenn es Vertretungen gibt, schreibe: "Für [Wochentag] gibt es folgende Vertretungen: [Vertretungen]"
        4. Bei Änderungen beachte folgende Regeln:
           - Wenn es die ersten beiden Stunden sind, sage "in den ersten beiden Stunden"
           - Bei 3. und 4. Stunde sage "in der dritten und vierten Stunde"
           - Bei 5. und 6. Stunde sage "in der fünften und sechsten Stunde"
           - Bei Nachmittagsunterricht:
             * Wenn der gesamte Nachmittagsunterricht ausfällt, sage nur "der Nachmittagsunterricht fällt aus"
             * Wenn nur ein Fach ausfällt, gib das genau an
        5. Bei Verlegungen:
           - Sage welches Fach ausgefallen ist, in welchen Stunden es jetzt Vertretung gibt, in welchem Fach, bei welchem Lehrer
        
        WICHTIG: Verwende NUR den Wochentag, niemals das Datum.
        """
        
        prompt = f"{instruction}\n\nVertretungsplan:\n\n{pdf_text}"
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Du bist ein Assistent, der Vertretungspläne präzise analysiert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result = response.choices[0].message.content
        logging.info("PROGRESS: Analysis complete")
        return result
    except Exception as e:
        logging.error("ERROR: Exception during OpenAI analysis: %s", str(e))
        return f"Error during analysis: {str(e)}"

def cleanup(pdf_path):
    """Clean up temporary files."""
    if pdf_path and os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
            logging.info("PROGRESS: Cleaned up temporary files")
        except Exception as e:
            logging.error("ERROR: Failed to clean up: %s", str(e))

def check_env_variables():
    """Check if all required environment variables are set."""
    required_vars = ["OPENAI_API_KEY", "EMAIL_USERNAME", "EMAIL_PASSWORD", "RECIPIENT_EMAIL", 
                     "AUTH_USERNAME", "AUTH_PASSWORD", "PDF_URL"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        logging.error("ERROR: Missing environment variables: %s", ", ".join(missing))
        return False
    logging.info("PROGRESS: All environment variables verified")
    return True

def main():
    """Main function to orchestrate the process."""
    logging.info("=== Starting Substitute Teacher Checker ===")
    mode = os.getenv("MODE", "email")
    logging.info("Mode: %s", mode)
    logging.info("PROGRESS: Starting analysis...")

    if not check_env_variables():
        return
    
    pdf_path = download_pdf()
    if not pdf_path:
        return
    
    analysis_result = analyze_with_openai(pdf_path)
    logging.info("ANALYSIS_RESULT: %s", analysis_result)
    
    if mode == "email":
        send_email(analysis_result)
    
    cleanup(pdf_path)
    logging.info("=== Substitute Teacher Checker Finished ===")

if __name__ == "__main__":
    main()
