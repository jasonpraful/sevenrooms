import datetime
import smtplib
import time

import config
import requests


def email(time):
    subject = "Booking is now available"
    body = f"Booking for {time} is now available.\n\n Book here: https://www.sevenrooms.com/reservations/{config.VENUE}"
    message = f"Subject: {subject}\n\n{body}"
    requests.post(
        url=f"https://api.telegram.org/{config.BOT_SECRET}/sendMessage",
        data={
            "chat_id": config.TELEGRAM_CHAT_ID,
            "text": message
        },
    ).json()
    if config.ENABLE_EMAIL:
        gmail_user = config.EMAIL_USERNAME
        gmail_password = config.EMAIL_PASSWORD
        gmail_smtp = config.EMAIL_SMTP_SERVER
        gmail_smtp_port = config.EMAIL_SMTP_PORT
        from_email = gmail_user
        to_email = config.EMAIL_TO
        try:
            server = smtplib.SMTP(gmail_smtp, gmail_smtp_port)
            server.ehlo()
            server.starttls()
            server.login(gmail_user, gmail_password)
            server.sendmail(from_email, to_email, message)
            server.close()
            print("Email sent!")
        except Exception as e:
            print(e)
            print("Something went wrong...")


runcount = 0
while True:
    print(runcount)
    converted_date = datetime.datetime.strptime(
        config.DATE_NEEDED, "%Y-%m-%d").strftime("%m-%d-%Y")
    runcount += 1
    response = requests.get(
        f"https://www.sevenrooms.com/api-yoa/availability/widget/range?venue={config.VENUE}&time_slot={config.MAIN_TIME}&party_size={config.NUM_PEOPLE}&halo_size_interval=16&start_date={converted_date}&num_days=1&channel=SEVENROOMS_WIDGET"
    )
    data = response.json()
    try:
        available = data["data"]["availability"][
            config.DATE_NEEDED][0]["times"]
        print(available[0]["time_iso"])
    except:
        print("No times available")
        time.sleep(config.RETRY_AFTER)
        continue
    times_i_want = [config.DATE_NEEDED + " " + s for s in config.TIMES_NEEDED]
    print(times_i_want)
    for i in available:
        if i["time_iso"] in times_i_want:
            print(i["time_iso"])
            print(i["access_persistent_id"])
            if i["access_persistent_id"] != None:
                print(i["time_iso"])
                print("Booking available")
                email(i["time_iso"])
    time.sleep(config.RETRY_AFTER)
