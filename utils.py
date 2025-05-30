
import re
from flask_mail import Message
from flask import current_app

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def send_email(to, subject, body):
    mail = current_app.extensions.get('mail')
    if mail is None:
        raise RuntimeError("L'extension Flask-Mail n'est pas initialisée.")
    msg = Message(subject, recipients=[to], body=body)
    mail.send(msg)
