from telegram import Update
from telegram.ext import ContextTypes

from .utils import (
    getTicketContext,
    closeRequest,
    updateRequestLog,
)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot = context.bot
    query = update.callback_query
    handler = query.from_user

    action, ticketID = query.data.split("_")[0], query.data.split("_")[1]
    ticketContext = getTicketContext(query.data.split("_")[-1])
    closeRequest(ticketID, tickerResult=action)

    updateRequestLog(
        ticketID,
        handler=handler.id,
    )

    await query.answer()

    if ticketContext.isEvidenceHasPhoto.all():
        await query.edit_message_caption(
            caption=f"Request ID: {ticketID} has been {action} by {handler.mention_html()}.",
            parse_mode="HTML",
        )
    else:
        await query.edit_message_text(
            text=f"Request ID: {ticketID} has been {action} by {handler.mention_html()}.",
            parse_mode="HTML",
        )

    await bot.send_message(
        ticketContext["requestMessageID"].values[0],
        f"Your Request with ID: {ticketID} has been {action}.",
    )


async def buttonForReport(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bot = context.bot
    query = update.callback_query
    handler = query.from_user

    query_data = query.data

    action = query_data.split("_")[0]
    chat_id = query_data.split("_")[1]
    message_id = query_data.split("_")[2]

    await query.answer()

    await query.edit_message_text(
        text=f"Request has been {action} by {handler.mention_html()}.",
        parse_mode="HTML",
    )
    emoji = "✅" if action == "processed" else "❌"
    await bot.edit_message_text(
        f"Request Status: {emoji} {action}.",
        chat_id=chat_id,
        message_id=message_id,
    )
