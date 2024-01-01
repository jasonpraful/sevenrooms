import requests
import smtplib
import time
import config
import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s SevenRooms Booking Checker - %(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("SevenRooms Booking Checker")


def generate_message(time, public_time_slot_description=None):
    """
    Generates a message for a booking that is now available.

    Args:
        time (str): The time slot available.
        public_time_slot_description (str, optional): The type of time slot available. for example: "Outdoor Seating". Defaults to None.

    Returns:
        str: The message to send.
    """
    subject = "Booking is now available"
    body = f"Booking for {time} is now available @ Seating: {public_time_slot_description if public_time_slot_description else 'Unknown'} .\n\n Book here: https://www.sevenrooms.com/reservations/{config.VENUE}"
    message = f"Subject: {subject}\n\n{body}"
    return message


def send_telegram(message):
    """
    Sends a message to a Telegram chat.

    Args:
        message (str): The message to send.

    Raises:
        Exception: If the message fails to send.
    """
    try:
        if not config.BOT_SECRET or not config.TELEGRAM_CHAT_ID:
            logger.error("Telegram bot secret or chat id not provided. Skipping.")
            return
        response = requests.post(
            url=f"https://api.telegram.org/{config.BOT_SECRET}/sendMessage",
            data={"chat_id": config.TELEGRAM_CHAT_ID, "text": message},
        )
        response.raise_for_status()
        logger.info("Telegram message sent.")
    except Exception as e:
        logger.error("Failed to send Telegram message.", exc_info=True)


def send_email(message):
    """
    Sends an email with the message if enabled.

    Args:
        message (str): The message to send.

    Raises:
        Exception: If the message fails to send.
    """
    if config.ENABLE_EMAIL:
        if not config.EMAIL_USERNAME or not config.EMAIL_PASSWORD:
            logger.error("Email username or password not provided. Skipping.")
            return
        try:
            gmail_user = config.EMAIL_USERNAME
            gmail_password = config.EMAIL_PASSWORD
            gmail_smtp = config.EMAIL_SMTP_SERVER
            gmail_smtp_port = config.EMAIL_SMTP_PORT
            from_email = gmail_user
            to_email = config.EMAIL_TO
            server = smtplib.SMTP(gmail_smtp, gmail_smtp_port)
            server.ehlo()
            server.starttls()
            server.login(gmail_user, gmail_password)
            server.sendmail(from_email, to_email, message)
            server.close()
            logger.info("Email sent!")
        except Exception as e:
            logger.error("Failed to send email.", exc_info=True)


def check_availability(date_needed):
    """
    Checks the availability of bookings for a given date.

    Args:
        date_needed (str): The date to check the booking availability for. Format: YYYY-MM-DD

    Returns:
        list: A list of available time slots.

    Raises:
        Exception: Raises an exception if the request fails.
    """
    converted_date = datetime.datetime.strptime(date_needed, "%Y-%m-%d").strftime(
        "%m-%d-%Y"
    )
    response = requests.get(
        f"https://www.sevenrooms.com/api-yoa/availability/widget/range?venue={config.VENUE}&time_slot={config.MAIN_TIME}&party_size={config.NUM_PEOPLE}&halo_size_interval=16&start_date={converted_date}&num_days=1&channel=SEVENROOMS_WIDGET"
    )
    data = response.json()
    try:
        available = data["data"]["availability"][date_needed][0]["times"]
        return available
    except Exception as e:
        logger.error("Failed to check availability.", exc_info=True)
        return None


def main():
    """
    Main function that runs the script.
    Polls the SevenRooms API for booking availability for the given dates, checks if there is a booking available for the times specified in the config, and sends a message to Telegram and/or email if a booking is available.
    """
    runcount = 0
    while True:
        logger.info(f"Run count: {runcount}")
        runcount += 1
        for date in config.DATES_NEEDED:
            available_slots = check_availability(date)
            times_i_want = [date + " " + s for s in config.TIMES_NEEDED]
            for i in available_slots:
                if i["time_iso"] in times_i_want and i["access_persistent_id"] != None:
                    slot_description = (
                        i["public_time_slot_description"]
                        if "public_time_slot_description" in i
                        else "Unknown"
                    )
                    logger.info(
                        msg=f"Booking available: {i['time_iso']} @ {slot_description}"
                    )
                    message = generate_message(
                        time=i["time_iso"],
                        public_time_slot_description=slot_description,
                    )
                    send_telegram(message)
                    send_email(message)
        time.sleep(config.RETRY_AFTER)


if __name__ == "__main__":
    main()
