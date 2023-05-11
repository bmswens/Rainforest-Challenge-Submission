# built in
import base64
import os
from email.message import EmailMessage

# 3rd party
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Based on https://developers.google.com/gmail/api/guides/sending

def get_creds():
    folder = os.path.dirname(os.path.abspath(__file__))
    creds_path = os.path.join(folder, 'token.json')
    creds = None
    if os.path.exists('token.json'):   
        creds = Credentials.from_authorized_user_file(
            creds_path,
            scopes=[
                "https://mail.google.com/"
            ]
        )
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', [
                "https://mail.google.com/"
            ])
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def send_mail(body, to, subject="MultiEarth Eval Update"):
    creds = get_creds()
    #delegated_creds = creds.with_subject('multiearth.evals@gmail.com')
    service = build("gmail", 'v1', credentials=creds)
    message = EmailMessage()

    message.set_content(body)

    message['To'] = to
    message['From'] = 'multiearth.evals@gmail.com'
    message['Cc'] = 'multiearth2023@gmail.com'
    message['Subject'] = subject

    # encoded message
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()) \
        .decode()

    create_message = {
        'raw': encoded_message
    }

    service.users().messages().send(
        userId="me", 
        body=create_message
    ).execute()


if __name__ == '__main__':
    send_mail("Test message.", "bmswens@gmail.com", "MultiEarth Eval Test")
