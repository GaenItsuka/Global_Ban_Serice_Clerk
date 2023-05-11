import os
import logging
import sys
import click

from Global_Ban_Service_Clerk import (
    message,
    command,
    callbackQuery,
    utils,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

logging.basicConfig(
    filename="GBSC_bot.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--ownerID", "ownerID", required=True, type=str, help="The owner of this bot."
)
def main(ownerID) -> None:
    GBBTYPE, EVIDENCE, EVIDENCE_PHOTO = range(3)

    logger.info("Running Pre-Flight setup.")
    utils.preflightCheck(ownerID)

    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(os.environ["BOT_TOKEN"]).build()

    # Gbb Request related commands
    application.add_handler(CommandHandler("start", command.GbbRequestCommand.start))
    application.add_handler(CommandHandler("report", command.GbbRequestCommand.report))
    application.add_handler(
        CommandHandler("showRequest", command.GbbRequestCommand.showRequest)
    )
    application.add_handler(
        CommandHandler(
            "showRemainRequests", command.GbbRequestCommand.showRemainRequests
        )
    )

    # Gbb related commands
    application.add_handler(CommandHandler("gbb", command.GlobanCommand.globalBan))
    application.add_handler(CommandHandler("enable_gbb", command.GlobanCommand.enableGbb))
    application.add_handler(CommandHandler("disable_gbb", command.GlobanCommand.disableGbb))
    application.add_handler(CommandHandler("check_gbb", command.GlobanCommand.checkGbb))
    application.add_handler(
        CommandHandler("addGbbGroup", command.GlobanCommand.addGlobalBanGroup)
    )
    application.add_handler(
        CommandHandler("removeGbbGroup", command.GlobanCommand.removeGlobalBanGroup)
    )

    # Utility commands
    application.add_handler(CommandHandler("setAdmin", command.UtilityCommand.setAdmin))
    application.add_handler(
        CommandHandler("revokeAdmin", command.UtilityCommand.revokeAdmin)
    )
    application.add_handler(CommandHandler("isAdmin", command.UtilityCommand.isAdmin))
    application.add_handler(CommandHandler("help", command.UtilityCommand.help))
    application.add_handler(
        CommandHandler("chatType", command.UtilityCommand.checkChatType)
    )
    application.add_handler(
        CommandHandler("userid", command.UtilityCommand.checkUserID)
    )

    # VIP command
    application.add_handler(
        CommandHandler("setHeadquarter", command.VIPCommand.setHeadquarter)
    )

    # Conversation Related
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("submit", command.GbbRequestCommand.submit)],
        states={
            GBBTYPE: [
                MessageHandler(
                    filters.Regex("^(Spam|Harassment|Test)$"), message.gbbtype
                )
            ],
            EVIDENCE: [
                MessageHandler(filters.TEXT & (~filters.COMMAND), message.evidenceText)
            ],
            EVIDENCE_PHOTO: [
                MessageHandler(filters.PHOTO, message.evidencePhoto),
                CommandHandler("skip", message.skip_photo),
            ],
        },
        fallbacks=[CommandHandler("cancel", message.cancel)],
        # entry_points=[],
    )
    application.add_handler(
        CallbackQueryHandler(
            callbackQuery.button, pattern="^(processed|rejected)_\w{16}"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            callbackQuery.buttonForReport, pattern="^(processed|rejected)_\-\d.*_\d.*$"
        )
    )
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
