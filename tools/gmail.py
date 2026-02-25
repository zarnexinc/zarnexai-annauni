import base64
import requests
from email.mime.text import MIMEText


def send_gmail(access_token: str, to: str, subject: str, body: str):
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject

    raw_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "raw": raw_message
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code >= 400:
        raise Exception(f"Gmail API error: {response.text}")