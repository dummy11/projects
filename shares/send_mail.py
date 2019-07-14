import smtplib
from email.mime.text import MIMEText
from email.header import Header

def send_mail(msg):
    mail_host="smtp.163.com"
    mail_user="feixiaduibing@163.com"
    mail_pass="feixiadui1"
    sender="feixiaduibing@163.com"
    receiver="feixiaduibing@163.com"
    subject="match code "
    message=MIMEText(msg, "plain", "utf-8")
    message['From']=sender
    message['To']=receiver
    message['Subject']=subject

    smtp=smtplib.SMTP()
    #smtp.connect(mail_host,25)
    smtp.connect(mail_host, 25)
    smtp.rset()
    #smtp.ehlo()
    smtp.starttls()
    smtp.login(mail_user, mail_pass)
    smtp.sendmail(sender, receiver, message.as_string())
    smtp.quit()

if __name__ == "__main__":
    send_mail("600666 \n")