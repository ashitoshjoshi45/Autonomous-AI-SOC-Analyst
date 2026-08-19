#ADDED ON 19-08-2026
import os
import requests # Used here to catch typical API connection/timeout exceptions
from celery import Celery

# Assuming these will be imported from your actual internal modules:
# from email_parser import parse_phishing_email
# from threat_intel import triage_phishing_artifacts

# Mock functions (replace these with your actual imports)
def parse_phishing_email(eml_file_path):
    pass

def triage_phishing_artifacts(artifacts):
    pass

# Initialize background worker app
# Using Redis as the default local message broker and result backend
app = Celery(
    'phishing_triage_worker',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
)

# Define a background task (allow up to 3 retries on failure)
# bind=True gives us access to 'self' to trigger retries
@app.task(bind=True, max_retries=3)
def process_reported_email_task(self, eml_file_path):
    try:
        # Step 1: Extract artifacts from the email file
        artifacts = parse_phishing_email(eml_file_path)
        
        # Step 2: Enrich and score artifacts via threat intel
        triage_report = triage_phishing_artifacts(artifacts)
        
        # Step 3: Return or log the final report for the SOC dashboard
        return triage_report

    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
        # Catch API timeout or connection error: retry after a 60-second delay
        raise self.retry(exc=exc, countdown=60)
    
    except Exception as e:
        # Optional: Catch-all for parsing errors, file not found, etc.
        # These won't retry automatically unless specified
        print(f"Failed to process {eml_file_path}: {e}")
        raise