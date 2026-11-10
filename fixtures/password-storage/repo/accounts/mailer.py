"""Outgoing email.

In production ``ACCOUNTS_SMTP_HOST`` is set and mail goes out over SMTP.
Everywhere else messages are written to an outbox folder as .eml files, which
is what the tests and local development read.
"""
import os
import smtplib
import uuid
from email.message import EmailMessage
from email.utils import formatdate

from . import config


class Mailer:
    def __init__(self, outbox_dir, smtp_host=None, smtp_port=None):
        self.outbox_dir = outbox_dir
        self.smtp_host = smtp_host if smtp_host is not None else config.SMTP_HOST
        self.smtp_port = smtp_port or config.SMTP_PORT

    def send(self, to, subject, body):
        msg = EmailMessage()
        msg["From"] = config.MAIL_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)
        msg.set_content(body)
        if self.smtp_host:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as smtp:
                smtp.send_message(msg)
        else:
            os.makedirs(self.outbox_dir, exist_ok=True)
            name = "%s.eml" % uuid.uuid4().hex
            with open(os.path.join(self.outbox_dir, name), "wb") as fh:
                fh.write(bytes(msg))
        return msg
