# bank-hapoalim-mail-notifier

This project is a hack meant to simplify my banks email reading experience.

My bank (Bank Hapoalim) occasionally sends me encrypted pdf messages. to open these messages i need to type an auto-generated password that i don't want to type each time i'm getting an email.

IMHO these pdf attachments should not be encrypted since

1. i'm already authenticated to my mailbox.
2. these messages never contain full credit card numbers nor passwords.


While i was wondering what's the risk of doing this complicated shit, i've decided to contact my bank explaining that this is BAD UX! and asking to toggle off this encryption feature. Guess what? they replied with "... to protect you we must encrypt! ..."

Well, my dear bank, this is my workaround for your bad UX solutions. I wish you hire someone to convince your Product Manager that you must allow this feature be toggled off


###So what it does?

This utility can be set to be a scheduled task and does the following:

1. Log in to gmail using IMAP. looking for unread mail labeled "Bank"
2. Gets emails' pdf attachments
3. Decrypt the attachments, re-sends the email to your inbox while using a relevant title and body


###Dependencies

```
sudo apt-get install pdftk
sudo apt-get install exiftool
sudo apt-get install poppler-utils
```

###Usage

- do you have 2 factor authentication enabled? to use this script, generate an [app password](https://security.google.com/settings/security/apppasswords)

first thing, edit `config.json` and fill in the blanks

```
{
  "email_address": "",
  "email_password": "",
  "pdf_password": ""
}
```

then you are ready to run `main.py`


###Installation

can be set as a scheduled task. to run it hourly on linux,
```
crontab -e
```

and add new line

```
0 * * * * /opt/bank-hapoalim-mail-notifier/src/main.py
```