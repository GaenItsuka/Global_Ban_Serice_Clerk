import toml
import secrets
import logging
import pandas as pd

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
    ContextTypes,
)

from .utils import (
    preflightCheck,
    checkIsAdmin,
    checkIsVIP,
    checkIsOwner,
    fetchRemainRequest,
    checkTableExist,
    createRequestLogTable,
    createRequestLog,
    createAdminLog,
    createAdminDB,
    setHQIndex,
    getHQIndex,
    deleteAdminLog,
)

logger = logging.getLogger(__name__)

async def showRemainRequest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    if checkIsAdmin(user.id):
        logger.info(f"Admin: {user.full_name}({user.id}) request the list of remaining requests.")
        remainRequestDF = fetchRemainRequest()

        if remainRequestDF.empty:
            await update.message.reply_text(
                "No pending request exists.",
            )
        else:
            print(1)
            recordList = remainRequestDF.to_dict("records")
            message_context = []
            for _dict in recordList:
                user_submit = User(
                    _dict["requestUser"], _dict["requestUserName"], False
                )

                _message_context = (
                    rf"▪RequstID: <pre>{_dict['requestID']}</pre>, 👤Submitee: {user_submit.mention_html()}"
                )
                
                message_context.append(_message_context)

            message_context.append(
                rf"Use <pre>/showRequest</pre> command with request ID to get detail information."
            )
            message = "\n======\n".join(message_context)
            await update.message.reply_html(
                message,
            )
            
                # keyboard = [
                #     [
                #         InlineKeyboardButton(
                #             "Done", callback_data=f"processed_{_dict['requestID']}"
                #         ),
                #         InlineKeyboardButton(
                #             "Reject", callback_data=f"rejected_{_dict['requestID']}"
                #         ),
                #     ]
                # ]

                # reply_markup = InlineKeyboardMarkup(keyboard)

                # message_template = (
                #     f"Request ticket with ID: {_dict['requestID']} received! \n"
                #     rf"The user who submitted the request: {user_submit.mention_html()}. "
                #     f"\nThe type of GBB request: {_dict['requestType']}. \n"
                #     rf"Evidence: {_dict['requestEvidence']}."
                # )
                # if _dict["isEvidenceHasPhoto"]:
                #     await update.message.reply_photo(
                #         photo=str(_dict["requestEvidencePhoto"]),
                #         parse_mode="HTML",
                #         caption=message_template,
                #         reply_markup=reply_markup,
                #     )
                # else:
                #     await update.message.reply_text(
                #         message_template,
                #         parse_mode="HTML",
                #         reply_markup=reply_markup,
                #     )
    else:
        logger.warning(f"User: {user.full_name}({user.id}) is trying to access the list of remaining requests.")
        await update.message.reply_html("You are not permit to do this.")


async def isAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    replied_message = update.message.reply_to_message
    replied_user = replied_message.from_user

    _isAdmin = checkIsAdmin(replied_user.id)

    keyStone = " a " if _isAdmin else " not a "
    message = rf"User: {replied_user.mention_html()} is{keyStone}administrator."

    await update.message.reply_html(message)


async def setAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    replied_message = update.message.reply_to_message
    replied_user = replied_message.from_user
    sender = update.effective_user

    if context.args != []:
        vipOption = context.args[0]

        if vipOption in ["VIP", "GENERAL"]:
            if checkIsVIP(sender.id):
                logger.info(f"VIP: {sender.full_name}({sender.id}) is trying to grant the permission to {replied_user.full_name}({replied_user.id}).")
                isVIP = True if vipOption == "VIP" else False
                createAdminLog(replied_user.id, isVIP)
                message = rf"User: {replied_user.mention_html()} has been configured as a administrator."
                logger.info(f"VIP: {sender.full_name}({sender.id}) has granted the permission to {replied_user.full_name}({replied_user.id}).")
            else:
                logger.warning(f"User: {sender.full_name}({sender.id}) is trying to grant the permission to {replied_user.full_name}({replied_user.id}).")
                message = "You are not permit to do this."
        else:
            logger.warning(f"User: {sender.full_name}({sender.id}) is trying to grant the permission to {replied_user.full_name}({replied_user.id}).")
            message = "No valid option provided. Please check again!"
    else:
        message = f"No option provided. Please check again!"

    await update.message.reply_html(message)


async def revokeAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    replied_message = update.message.reply_to_message
    replied_user = replied_message.from_user
    sender = update.effective_user

    if checkIsVIP(sender.id) and not checkIsOwner(replied_user.id):
        try:
            logger.warning(f"Admin: {sender.full_name}({sender.id}) is trying to revoke the permission of {replied_user.full_name}({replied_user.id}).")
            deleteAdminLog(replied_user.id)
            message = rf"User: {replied_user.mention_html()} has been revoked."
        except Exception as e:
            logger.warning(f"An error occured when admin: {sender.full_name}({sender.id}) is trying to revoke the permission of {replied_user.full_name}({replied_user.id}).")
            message = f"An error occured: {e}."
    elif checkIsOwner(replied_user.id):
        logger.warning(f"User: {sender.full_name}({sender.id}) is trying to revoke the permission of {replied_user.full_name}({replied_user.id}).")
        message = "Owner is not able to revoke. Your action has been recorded."
    else:
        message = "You are not permit to do this."

    await update.message.reply_html(message)


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    HQIndex = getHQIndex()
    bot = context.bot
    replied_message = update.message.reply_to_message
    replied_user = replied_message.from_user
    sender = update.effective_user
    chat = update.effective_chat

    if replied_message is not None and context.args != []:
        logger.info(f"User: {sender.first_name}({sender.id}) has reported a GBB request in chat: {chat.full_name}({chat.id}).")
        comment = "_".join(context.args)
        mesesage = (
            rf"User: {sender.mention_html()} has reported a GBB reuqest in {chat.mention_html()}."
            "\n"
            rf"Reported user: {replied_user.mention_html()}(<pre>{replied_user.id}</pre>)"
            "\n"
            rf"Message link: {replied_message.link}"
            f"\nComment: {comment}."
        )

        bot_reply = await update.message.reply_text("The message has been reported.")

        keyboard = [
            [
                InlineKeyboardButton(
                    "Done", callback_data=f"processed_{chat.id}_{bot_reply.message_id}"
                ),
                InlineKeyboardButton(
                    "Reject", callback_data=f"rejected_{chat.id}_{bot_reply.message_id}"
                ),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await bot.send_message(
            HQIndex,
            mesesage,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
    elif replied_message is not None and context.args == []:
        await update.message.reply_text(
            "No comment message exists. Please send a report with comment again."
        )
    else:
        await update.message.reply_text(
            "No replied message exists. Please check again."
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /start is issued."""
    user = update.message.from_user
    start_message = (
        rf"Hi {user.mention_html()}! "
        "I am a bot that can help you to submit a gbb request to administrators.\n"
        "Use <a>/submit</a> to submit a ticket."
    )
    await update.message.reply_html(start_message)


async def setHeadquarter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Set the headquarter that the request ticket to broadcast."""

    chat = update.effective_chat
    user = update.effective_user

    if checkIsVIP(user.id):
        try:
            logger.warning(f"Admin: {user.full_name}({user.id}) is trying to change the HQ.")
            setHQIndex(chat.id)
            await update.message.reply_html("Complete!")
            logger.warning(f"The HQ group has been changed by admin: {user.full_name}({user.id}).")

        except Exception as e:
            await update.message.reply_html(f"An error occured: {e}.")
            log_message = (
                f"An error occured when admin: {user.full_name}({user.id}) is trying to change the HQ.\n"
                f"Exception: {e}"
            )
            logger.warning(log_message)

    else:
        logger.info(f"User: {user.first_name}({user.id}) is trying to change the HQ.")
        await update.message.reply_html("You are not permit to do this.")


async def submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about their requests."""
    ticketID = secrets.token_hex(8)

    user = update.message.from_user
    chat = update.effective_chat

    logger.info(f"User: {user.first_name}({user.id}) submit a new ticket with ID: {ticketID}")

    createRequestLog(
        ticketID,
        ticketUser=user.id,
        ticketUserName=user.first_name,
        ticketMessageID=chat.id,
    )

    reply_keyboard = [["Spam", "Harassment", "Test"]]

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

    return 0

async def showRequest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    if context.args != []:
        ticketID = context.args[0]
        remainRequestDF = fetchRemainRequest()
        
        desiredRequest = remainRequestDF.query(f"requestID == @ticketID")

        _dict = desiredRequest.to_dict("records")[0]

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
        message_template = (
            f"Request ticket with ID: {_dict['requestID']} received! \n"
            rf"The user who submitted the request: {user_submit.mention_html()}. "
            f"\nThe type of GBB request: {_dict['requestType']}. \n"
            rf"Evidence: {_dict['requestEvidence']}."
        )
        if _dict["isEvidenceHasPhoto"]:
            await update.message.reply_photo(
                photo=str(_dict["requestEvidencePhoto"]),
                parse_mode="HTML",
                caption=message_template,
                reply_markup=reply_markup,
            )
        else:
            await update.message.reply_text(
                message_template,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )

    elif len(context.args) > 1:
        await update.message.reply_html(
            'Cannot search more than one request at the same time. Please check again.',
        )
    else:
        await update.message.reply_html(
            'No argument found. Abort!',
        )

    
