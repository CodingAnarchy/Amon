import smtplib


def send_email(fromaddr, toaddr, msg):
    # Credentials (needed for login)
    user = '<redacted>'
    password = '<redacted>'

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(user, password)
    server.sendmail(fromaddr, toaddr, msg)
    server.quit()