import logging

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)

from telegram import (
    Update,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from .utils import (
    getLatestTicket,
    updateRequestLog,
    getHQIndex,
)

logger = logging.getLogger(__name__)


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

    return 1


async def evidenceText(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected gender and asks for a photo."""
    user = update.message.from_user
    text = update.message.text
    latestTicket = getLatestTicket(user.id)

    updateRequestLog(
        latestTicket.requestID,
        requestEvidence=text,
    )

    logger.info("GBB evidence from %s: %s", user.first_name, text)
    await update.message.reply_text(
        "I see! Are you going to send a photo as a supplementary material? If not, send /skip.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return 2


async def postSubmissionAction(user, bot):
    HQIndex = getHQIndex()
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
    message_template = (
        f"A new GBB request ticket with ID: {completeRequest.requestID} received! \n"
        rf"The user who submitted the request: {user.mention_html()}. "
        f"\nThe type of GBB request: {completeRequest.requestType}. \n"
        rf"Evidende: {completeRequest.requestEvidence}."
    )
    if completeRequest.isEvidenceHasPhoto:
        await bot.send_photo(
            HQIndex,
            photo=str(completeRequest.requestEvidencePhoto),
            parse_mode="HTML",
            caption=message_template,
            reply_markup=reply_markup,
        )
    else:
        await bot.send_message(
            HQIndex,
            message_template,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )


async def evidencePhoto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected gender and asks for a photo."""
    bot = context.bot
    user = update.message.from_user
    photo = update.message.photo
    latestTicket = getLatestTicket(user.id)

    evidence = photo[1].file_id

    updateRequestLog(
        latestTicket.requestID,
        requestEvidencePhoto=evidence,
        isEvidenceHasPhoto=True,
    )

    logger.info("GBB evidence from %s: %s", user.first_name, photo)
    await update.message.reply_text(
        "I see! Please be patient and wait for admin's review. ",
        reply_markup=ReplyKeyboardRemove(),
    )

    await postSubmissionAction(user, bot)

    return ConversationHandler.END


async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    bot = context.bot
    user = update.message.from_user
    logger.info("User %s did not send a photo.", user.first_name)

    await postSubmissionAction(user, bot)

    await update.message.reply_text(
        "I see! Please be patient and wait for admin's review. "
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text("Bye!", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END
