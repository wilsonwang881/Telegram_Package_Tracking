import logging
import requests
import xml.etree.ElementTree as ET
import os
from datetime import datetime

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


USPSTrackingNumbers = {}
deliveredUSPSTrackingNumbers = {}
USPS_TOKEN = os.getenv('USPS_TOKEN')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Use /USPS \\<track number\\> to add a new package track\n\nUse /USPS to track all added USPS packages', parse_mode='MarkdownV2')


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    res = "\"" + update.message.text + "\" is not a valid command. Try /help."
    update.message.reply_text(res)


def removeDeliveredUSPSTracking(context: CallbackContext) -> None:
    """Send the alarm message."""
    job = context.job
    global deliveredUSPSTrackingNumbers
    timenow = datetime.now()
    recordsToRemove = []
    for key in deliveredUSPSTrackingNumbers:
        if ((timenow - deliveredUSPSTrackingNumbers[key]).total_seconds()) > (23 * 3600):
            USPSTrackingNumbers.pop(key)
            recordsToRemove.append(key)
    
    for el in recordsToRemove:
        deliveredUSPSTrackingNumbers.pop(el)


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def queryUSPS(update: Update, context: CallbackContext) -> None:
    """Query USPS API to get the tracking details"""
    if len(context.args) > 0:
        USPSTrackingNumbers[context.args[0]] = ''
    elif USPSTrackingNumbers == {}:
        update.message.reply_text("Please add tracking numbers\\!", parse_mode='MarkdownV2')
        return

    headers = {'Content-Type': 'application/xml'} # set what your server accepts

    recordsToPop = []

    for key in USPSTrackingNumbers:
        xmlRequest = """https://secure.shippingapis.com/ShippingAPI.dll?API=TrackV2&XML=<?xml version='1.0' encoding='utf-8'?><TrackRequest USERID=\"""" + USPS_TOKEN + "\">"""
        xmlRequest = xmlRequest + '<TrackID ID=\"' + key + '\"></TrackID>'
        xmlRequest = xmlRequest + '</TrackRequest>'
    
        res = requests.post(xmlRequest, headers=headers).text

        parsedXMLRoot = ET.fromstring(res)

        reassembledRes = "*Track ID* \n\n"

        reassembledRes = reassembledRes + key + '\n\n'

        reassembledRes = reassembledRes + "*Track Summary* \n\n"

        for child in parsedXMLRoot.iter('TrackSummary'):
            reassembledRes = reassembledRes + child.text + '\n\n'
            if "try again later" in child.text:
                recordsToPop.append(key)
            if "was delivered" in child.text:
                deliveredUSPSTrackingNumbers[key] = datetime.now()
                chat_id = update.message.chat_id
                job_removed = remove_job_if_exists(str(chat_id), context)
                context.job_queue.run_once(removeDeliveredUSPSTracking, 24 * 3600, context=chat_id, name=str(chat_id))

        reassembledRes = reassembledRes + "*Track Details* \n\n"

        for child in parsedXMLRoot.iter('TrackDetail'):
            reassembledRes = reassembledRes + child.text + '\n\n'

        reassembledRes = reassembledRes.replace("_", "\\_").replace("[", "\\[").replace("`", "\\`").replace(".", "\\.").replace("#", "\\#").replace("=", "\\=").replace('-', '\\-')
        update.message.reply_text(reassembledRes, parse_mode='MarkdownV2') #

    for record in recordsToPop:
        USPSTrackingNumbers.pop(record)


def clearRecords(update: Update, context: CallbackContext) -> None:
    USPSTrackingNumbers = {}
    update.message.reply_text("Cleared tracking records!")


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TELEGRAM_BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("USPS", queryUSPS))
    dispatcher.add_handler(CommandHandler("clear", clearRecords))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()