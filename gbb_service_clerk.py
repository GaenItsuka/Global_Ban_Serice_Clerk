import os
import secrets
import logging
import sqlite3
import pandas as pd
import toml
import matplotlib.pyplot as plt
from PIL import Image
from datetime import datetime
from telegram import __version__ as TG_VER
from functools import partial
from io import StringIO


from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    User,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

GBBTYPE, EVIDENCE = range(2)

############################################################
#
#               Bacis Utilities
#
############################################################


def createConnection(DBName="GbbRequestDB.db"):
    conn = sqlite3.connect(DBName)
    cursor = conn.cursor()
    return conn, cursor


def checkTableExist(tableName, DBName="GbbRequestDB.db"):
    conn, cursor = createConnection(DBName)
    response = cursor.execute(
        """SELECT name 
            FROM sqlite_schema 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%';
        """
    )
    tableList = response.fetchall()
    conn.close()
    if tableList == []:
        result = False
    else:
        result = True if tableName in tableList[0] else False
    return result


############################################################
#
#               Request record utilities
#
############################################################


def createRequestLogTable():
    conn, cursor = createConnection()
    response = cursor.execute(
        """CREATE TABLE IF NOT EXISTS GbbRequest (
            requestID text,
            requestMessageID text,
            requestDate text,
            requestUser text,
            requestUserName text,
            requestType text,
            requestEvidence text,
            isEvidencePhoto bool,
            processed bool,
            result text
            );
        """
    )
    result = response.fetchall()
    return result


def createRequestLog(
    ticketID: str,
    ticketMessageID: str = None,
    ticketUser: str = None,
    ticketUserName: str = None,
    ticketType: str = None,
    requestEvidence: str = None,
    isEvidencePhoto: bool = False,
):
    conn, cursor = createConnection()
    response = cursor.execute(
        f"""INSERT INTO GbbRequest (
            requestID,
            requestMessageID,
            requestDate,
            requestUser,
            requestUserName,
            requestType,
            requestEvidence,
            isEvidencePhoto,
            processed,
            result
        ) 
        VALUES (
            "{ticketID}",
            "{ticketMessageID}",
            "{datetime.now()}",
            "{ticketUser}",
            "{ticketUserName}",
            "{ticketType}",
            "{requestEvidence}",
            {isEvidencePhoto},
            False,
            "None"
        );
        """
    )
    conn.commit()
    conn.close()


def getLatestTicket(user):
    conn, cursor = createConnection()
    df = pd.read_sql(f"SELECT * FROM GbbRequest WHERE requestUser = {user}", conn)
    df = df.iloc[-1]
    return df


def getTicketContext(ticketID):
    conn, cursor = createConnection()
    df = pd.read_sql(f"SELECT * FROM GbbRequest WHERE requestID = '{ticketID}'", conn)
    return df


def updateRequestLog(
    ticketID: str,
    ticketUser: str = None,
    ticketType: str = None,
    requestEvidence: str = None,
    isEvidencePhoto: bool = None,
):
    conn, cursor = createConnection()
    if ticketType is not None and requestEvidence is None:
        print("*" * 80)
        response = cursor.execute(
            f"""UPDATE GbbRequest
            SET requestType = "{ticketType}"
            WHERE requestID = "{ticketID}"
            """
        )
    elif requestEvidence is not None:
        response = cursor.execute(
            f"""UPDATE GbbRequest
            SET requestEvidence = "{requestEvidence}",
                isEvidencePhoto = {isEvidencePhoto}
            WHERE requestID = "{ticketID}"
            """
        )
    conn.commit()
    conn.close()


def closeRequest(
    ticketID: str,
    tickerResult: bool = False,
):
    conn, cursor = createConnection()
    response = cursor.execute(
        f"""UPDATE GbbRequest
        SET processed = True,
            result = "{tickerResult}"
        WHERE requestID = "{ticketID}"
        """
    )
    conn.commit()
    conn.close()


def fetchRemainRequest():
    conn, cursor = createConnection()
    response = pd.read_sql("SELECT * FROM GbbRequest WHERE processed = False", conn)
    return response


############################################################
#
#               HQ utilities
#
############################################################


def setHQIndex(chatID):
    cfg = toml.load("config.toml")
    cfg["Headquarter"]["chatID"] = chatID
    with open("config.toml", "w") as file:
        savedCfg = toml.dump(cfg, file)


def getHQIndex():
    cfg = toml.load("config.toml")
    return cfg["Headquarter"]["chatID"]


############################################################
#
#               Trust user utilities
#
############################################################


def createAdminDB():
    conn, cursor = createConnection(DBName="Admin.db")
    response = cursor.execute(
        """CREATE TABLE IF NOT EXISTS Admin (
            UID text,
            CLASS text,
            IsOWNER bool,
            UNIQUE(UID)
            );
        """
    )
    cursor.execute(
        f"""INSERT INTO Admin (UID, CLASS, IsOWNER) 
        VALUES ("360756730", "admin", {True});
        """
    )
    result = response.fetchall()
    conn.commit()
    conn.close()


def createAdminLog(UID):
    conn, cursor = createConnection(DBName="Admin.db")
    response = cursor.execute(
        f"""INSERT INTO Admin (UID, CLASS, IsOWNER) 
        VALUES ("{UID}", "admin", {False});
        """
    )
    result = response.fetchall()
    conn.commit()
    conn.close()
    return result


def deleteAdminLog(UID):
    conn, cursor = createConnection(DBName="Admin.db")
    response = cursor.execute(
        f"""DELETE FROM Admin 
        WHERE UID = "{UID}"; 
        """
    )
    result = response.fetchall()
    conn.commit()
    conn.close()
    return result


def checkIsAdmin(UID):
    conn, cursor = createConnection(DBName="Admin.db")
    # adminDF = pd.read_sql("SELECT UID FROM Admin WHERE CLASS = 'admin';", conn)
    response = cursor.execute("SELECT UID FROM Admin WHERE CLASS = 'admin';").fetchall()
    adminList = [record_tuple[0] for record_tuple in response]

    print(adminList, response)

    result = str(UID) in adminList
    return result


############################################################
#
#               Commands
#
############################################################


async def showRemainRequest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    _isAdmin = checkIsAdmin(user.id)
    if _isAdmin:
        remainRequestDF = fetchRemainRequest()

        if remainRequestDF.empty:
            await update.message.reply_text(
                "No pending request exists.",
            )
        else:
            recordList = remainRequestDF.to_dict("records")

            for _dict in recordList:
                user_submit = User(
                    _dict["requestUser"], _dict["requestUserName"], False
                )
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "Done", callback_data=f"processed_{_dict['requestID']}"
                        ),
                        InlineKeyboardButton(
                            "Reject", callback_data=f"rejected_{_dict['requestID']}"
                        ),
                    ]
                ]

                reply_markup = InlineKeyboardMarkup(keyboard)
                if _dict["isEvidencePhoto"]:
                    message_template = (
                        f"Request ticket with ID: {_dict['requestID']} received! \n"
                        rf"The user who submitted the request: {user_submit.mention_html()}. "
                        f"\nThe type of GBB request: {_dict['requestType']}. \n"
                        rf"Evidende: Please check the attachment."
                    )

                    await update.message.reply_photo(
                        photo=str(_dict["requestEvidence"]),
                        parse_mode="HTML",
                        caption=message_template,
                        reply_markup=reply_markup,
                    )
                else:
                    message_template = (
                        f"A new GBB request ticket with ID: {_dict['requestID']} received! \n"
                        rf"The user who submitted the request: {user_submit.mention_html()}. "
                        f"\nThe type of GBB request: {_dict['requestType']}. \n"
                        rf"Evidence: {_dict['requestEvidence']}."
                    )
                    await update.message.reply_text(
                        message_template,
                        parse_mode="HTML",
                        reply_markup=reply_markup,
                    )
    else:
        await update.message.reply_html("You are not permit to do this.")


async def isAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    replied_message = update.message.reply_to_message
    replied_user = replied_message.from_user

    _isAdmin = checkIsAdmin(replied_user.id)

    if _isAdmin:
        message = rf"User: {replied_user.mention_html()} is a administrator."
    else:
        message = rf"User: {replied_user.mention_html()} is not a administrator."

    await update.message.reply_html(message)


async def setAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    replied_message = update.message.reply_to_message
    replied_user = replied_message.from_user
    sender = update.effective_user
    if not checkTableExist("Admin", DBName="Admin.db"):
        createAdminDB()

    _isAdmin = checkIsAdmin(sender.id)

    if _isAdmin:
        try:
            createAdminLog(replied_user.id)
            message = rf"User: {replied_user.mention_html()} has been configured as a administrator."
        except Exception as e:
            message = f"An error occured: {e}."
    else:
        message = "You are not permit to do this."

    await update.message.reply_html(message)


async def revokeAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    replied_message = update.message.reply_to_message
    replied_user = replied_message.from_user
    sender = update.effective_user

    _isAdmin = checkIsAdmin(sender.id)

    if _isAdmin:

        try:
            deleteAdminLog(replied_user.id)
            message = rf"User: {replied_user.mention_html()} has been revoked."
        except Exception as e:
            message = f"An error occured: {e}."
    else:
        message = "You are not permit to do this."

    await update.message.reply_html(message)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /start is issued."""
    user = update.message.from_user
    start_message = (
        rf"Hi {user.mention_html()}! "
        "I am a bot that can help you to submit a gbb request to administrators.\n"
        "Use <a>/submit</a> a ticket."
    )
    await update.message.reply_html(start_message)


async def setHeadquarter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Set the headquarter that the request ticket to broadcast."""
    chat = update.effective_chat
    user = update.effective_user

    if user.id == 360756730:
        try:
            setHQIndex(chat.id)

            await update.message.reply_html("Complete!")
        except Exception as e:
            await update.message.reply_html(f"An error occured: {e}.")
    else:
        await update.message.reply_html("You are not permit to do this.")


async def submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about their requests."""
    ticketID = secrets.token_hex(8)
    user = update.message.from_user
    chat = update.effective_chat
    if not checkTableExist("GbbRequest"):
        createRequestLogTable()

    createRequestLog(
        ticketID,
        ticketUser=user.id,
        ticketUserName=user.first_name,
        ticketMessageID=chat.id,
    )

    reply_keyboard = [["Spam", "Harassment"]]

    submitResponse = (
        "Hi! Please choose the type of gbb you want to submit.\n"
        rf"To cancel the submission, please use <a>/cancel</a> command."
    )

    await update.message.reply_text(
        submitResponse,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="What kinds of gbb request?",
        ),
        parse_mode="HTML",
    )

    return GBBTYPE


############################################################
#
#               Conversations
#
############################################################


async def gbbtype(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected gender and asks for a photo."""

    user = update.message.from_user

    latestTicket = getLatestTicket(user.id)

    updateRequestLog(
        latestTicket.requestID,
        ticketType=update.message.text,
    )

    logger.info("GBB type of request from %s: %s", user.first_name, update.message.text)
    await update.message.reply_text(
        "I see! Please send me an evidence, " "so I know what happend to you.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return EVIDENCE


async def evidence(update: Update, context: ContextTypes.DEFAULT_TYPE, bot=None) -> int:
    """Stores the selected gender and asks for a photo."""
    # NordlichtChatID = -640476491
    HQIndex = getHQIndex()
    user = update.message.from_user
    photo = update.message.photo
    text = update.message.text
    latestTicket = getLatestTicket(user.id)

    isEvidencePhoto = False if photo == () else True

    evidence = photo[1].file_id if isEvidencePhoto else text

    updateRequestLog(
        latestTicket.requestID,
        requestEvidence=evidence,
        isEvidencePhoto=isEvidencePhoto,
    )

    logger.info("GBB evidence from %s: %s, %s", user.first_name, text, photo)
    await update.message.reply_text(
        "I see! Please be patient and wait for admin's review. ",
        reply_markup=ReplyKeyboardRemove(),
    )

    completeRequest = getLatestTicket(user.id)

    keyboard = [
        [
            InlineKeyboardButton(
                "Done", callback_data=f"processed_{completeRequest.requestID}"
            ),
            InlineKeyboardButton(
                "Reject", callback_data=f"rejected_{completeRequest.requestID}"
            ),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if completeRequest.isEvidencePhoto:
        message_template = (
            f"A new GBB request ticket with ID: {completeRequest.requestID} received! \n"
            rf"The user who submitted the request: {user.mention_html()}. "
            f"\nThe type of GBB request: {completeRequest.requestType}. \n"
            rf"Evidende: Please check the attachment."
        )
        await bot.send_photo(
            HQIndex,
            photo=str(evidence),
            parse_mode="HTML",
            caption=message_template,
            reply_markup=reply_markup,
        )
    else:
        message_template = (
            f"A new GBB request ticket with ID: {completeRequest.requestID} received! \n"
            rf"The user who submitted the request: {user.mention_html()}. "
            f"\nThe type of GBB request: {completeRequest.requestType}. \n"
            rf"Evidence: {completeRequest.requestEvidence}."
        )
        await bot.send_message(
            HQIndex,
            message_template,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )

    return ConversationHandler.END


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE, bot=None) -> None:
    query = update.callback_query
    action, ticketID = query.data.split("_")[0], query.data.split("_")[1]
    ticketContext = getTicketContext(query.data.split("_")[-1])
    closeRequest(ticketID, tickerResult=action)
    await query.answer()

    await query.edit_message_text(text=f"Request ID: {ticketID} has been {action}.")
    await bot.send_message(
        ticketContext["requestMessageID"].values[0],
        f"Your Request with ID: {ticketID} has been {action}.",
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text("Bye!", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


############################################################
#
#               Main
#
############################################################


def main() -> None:

    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(os.environ["BOT_TOKEN"]).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setAdmin", setAdmin))
    application.add_handler(CommandHandler("revokeAdmin", revokeAdmin))
    application.add_handler(CommandHandler("isAdmin", isAdmin))
    application.add_handler(CommandHandler("set_headquarter", setHeadquarter))
    application.add_handler(CommandHandler("showRemainRequest", showRemainRequest))
    partialEvidence = partial(evidence, bot=application.bot)
    partialButton = partial(button, bot=application.bot)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("submit", submit)],
        states={
            GBBTYPE: [MessageHandler(filters.Regex("^(Spam|Harassment)$"), gbbtype)],
            EVIDENCE: [MessageHandler(filters.TEXT | filters.PHOTO, partialEvidence)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(CallbackQueryHandler(partialButton))

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
