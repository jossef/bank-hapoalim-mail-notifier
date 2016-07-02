#!/usr/bin/env python
# -*- coding: utf-8 -*-

import imaplib
import smtplib

import email
import subprocess
import tempfile
import os
import shutil
import re
import json

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def read_config():
    with open(os.path.join(SCRIPT_DIR, 'config.json')) as f:
        config = json.loads(f.read())
        return config['email_address'], config['email_password'], config['pdf_password']


def get_unread_mail_attachments(email_address, email_password, label_name):
    imap = imaplib.IMAP4_SSL('imap.gmail.com')
    imap.login(email_address, email_password)
    imap.select(label_name)
    typ, data = imap.search(None, 'UnSeen')
    email_ids = data[0].split()
    for email_id in email_ids:
        try:
            typ, data = imap.fetch(email_id, '(BODY.PEEK[])')
            email_body = data[0][1]
            mail = email.message_from_string(email_body)
            if mail.get_content_maintype() != 'multipart':
                continue

            for part in mail.walk():
                if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                    continue

                attachment_data = part.get_payload(decode=True)
                yield attachment_data

        finally:
            imap.store(email_id, '+FLAGS', '\Seen')

    imap.close()
    imap.logout()


def send_mail(email_address, email_password, send_from, send_to, subject, text, attachments=None):
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = send_to
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text, _charset="UTF-8"))

    for attachment in attachments or []:
        with open(attachment, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=os.path.basename(attachment)
            )

            attachment_file_name = os.path.basename(attachment)
            part['Content-Disposition'] = 'attachment; filename="{filename}"'.format(filename=attachment_file_name)
            msg.attach(part)

    smtp = smtplib.SMTP('smtp.gmail.com', 587)
    smtp.starttls()
    smtp.login(email_address, email_password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()


def get_pdf_title(pdf_file_path):
    try:
        exif_data_json = subprocess.check_output(['exiftool', '-j', pdf_file_path])
        exif_data = json.loads(exif_data_json)

        return exif_data[0]['Title']

    except:
        # For the cases the exif is missing
        return ''


def get_pdf_content(pdf_file_path):
    temporary_dir_path = tempfile.mkdtemp()

    try:
        pdf_content_file_path = os.path.join(temporary_dir_path, 'content.txt')
        os.system('pdftotext {pdf_file_path} {pdf_content_file_path}'.format(pdf_file_path=pdf_file_path,
                                                                             pdf_content_file_path=pdf_content_file_path))

        with open(pdf_content_file_path) as f:
            return f.read().decode('utf-8')
    finally:
        shutil.rmtree(temporary_dir_path)


def decrypt_pdf(encrypted_file_path, decrypted_file_path, pdf_password):
    os.system('pdftk {encrypted_file_path} input_pw {pdf_password} output {decrypted_file_path}'.format(
        encrypted_file_path=encrypted_file_path, decrypted_file_path=decrypted_file_path, pdf_password=pdf_password))


def parse_hebrew_message(text):
    lines = text.splitlines()
    lines = filter(lambda line: re.match(ur'^(.*)([א-ת]+)(.*)$', line), lines)
    return '\n'.join(lines)


def main():
    email_address, email_password, pdf_password = read_config()

    for attachment in get_unread_mail_attachments(email_address, email_password, 'Bank'):

        temporary_dir_path = tempfile.mkdtemp()

        try:

            encrypted_file_path = os.path.join(temporary_dir_path, 'encrypted.pdf')
            decrypted_file_path = os.path.join(temporary_dir_path, 'decrypted.pdf')

            with open(encrypted_file_path, 'wb') as w:
                w.write(attachment)

            decrypt_pdf(encrypted_file_path, decrypted_file_path, pdf_password)

            title = get_pdf_title(decrypted_file_path)
            if not title:
                title = u'דואר מהבנק'

            body = get_pdf_content(decrypted_file_path)
            body = parse_hebrew_message(body)
            if not body:
                body = u''

            send_mail(email_address, email_password, email_address, email_address, title, body, [decrypted_file_path])
        finally:
            shutil.rmtree(temporary_dir_path)


if __name__ == '__main__':
    main()
