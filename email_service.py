import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_fraud_alert_email(supplier_name: str, contact_email: str, fraud_count: int):
    """
    Sends an email alert to the supplier when their fraud instances cross a threshold.
    """
    if not contact_email or contact_email == "Unknown":
        print(f"Could not send email for {supplier_name}: No contact email available.")
        return False
        
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    
    if not all([smtp_server, smtp_port, smtp_user, smtp_pass]):
        print("SMTP credentials not fully configured in .env. Skipping email.")
        return False
        
    subject = f"URGENT: Suspicious Activity Alert for {supplier_name}"
    body = f"""
    Dear {supplier_name} Team,
    
    This is an automated administrative alert from the MTC Verification System.
    
    We have detected a significantly high number ({fraud_count}) of recent Material Test Certificates (MTCs) 
    purportedly issued by your company that have failed our anti-fraud verifications.
    
    This may indicate that fraudulent or forged documents are being circulated under your name.
    Please investigate this matter immediately to protect the integrity of your supply chain.
    
    Best Regards,
    The MTC Verification Security Team
    """

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = contact_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        print(f"Fraud alert email successfully sent to {contact_email} for {supplier_name}.")
        return True
    except Exception as e:
        print(f"Failed to send email to {contact_email}: {e}")
        return False
