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
    Chat,
)

from telegram.error import (
    ChatMigrated,
)

from telegram.ext import (
    Application,
    ContextTypes,
)

from .decorator import (
    HQOnly,
    NotPrivate,
    PrivateOnly,
    GbbFilter,
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
    createGbbGroupLog,
    getGbbGroupLog,
    updateGbbGroupLog,
    removeGbbGroupLog,
    configGbbCommand,
    checkGbbConfig,
)

logger = logging.getLogger(__name__)


class GlobanCommand:
    @staticmethod
    @HQOnly
    async def enableGbb(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user

        if checkIsAdmin(user.id) or checkIsVIP(user.id):
            logger.info(
                f"Admin {user.full_name}({user.id}) trying to enable Gbb command."
            )
            configGbbCommand("1")
            message = "Done"
        else:
            logger.warning(
                f"User {user.full_name}({user.id}) trying to enable Gbb command."
            )
            message = "You are not permit to do that. Your action will be recorded."
        await update.message.reply_html(message)

    @staticmethod
    @HQOnly
    async def disableGbb(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user

        if checkIsAdmin(user.id) or checkIsVIP(user.id):
            logger.info(
                f"Admin {user.full_name}({user.id}) trying to disable Gbb command."
            )
            configGbbCommand("0")
            message = "Done"
        else:
            logger.warning(
                f"User {user.full_name}({user.id}) trying to disable Gbb command."
            )
            message = "You are not permit to do that. Your action will be recorded."
        await update.message.reply_html(message)

    @staticmethod
    @HQOnly
    async def checkGbb(update: Update, context: ContextTypes.DEFAULT_TYPE):
        status = checkGbbConfig()

        message = rf"Gbb command enabled: {status}."

        await update.message.reply_html(message)

    @staticmethod
    @NotPrivate
    async def removeGlobalBanGroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat
        bot = context.bot

        if checkIsAdmin(user.id) or checkIsVIP(user.id):
            logger.info(
                f"Admin {user.full_name}({user.id}) trying to remove chat {chat.id} from list."
            )
            removeGbbGroupLog(chat.id)
            message = "Done"
        else:
            logger.warning(
                f"User {user.full_name}({user.id}) trying to remove chat {chat.id} from list."
            )
            message = "You are not permit to do that. Your action will be recorded."

        await update.message.reply_html(message)

    @staticmethod
    @GbbFilter
    async def globalBan(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        bot = context.bot

        if context.args != []:
            if checkIsAdmin(user.id) or checkIsVIP(user.id):
                logger.info(f"Admin {user.full_name}({user.id}) send a gbb request.")

                groupList = getGbbGroupLog().groupid.to_list()
                groupNameList = getGbbGroupLog().groupname.to_list()

                targetUser = context.args[0]

                for groupid, groupname in zip(groupList, groupNameList):
                    chat = await bot.get_chat(int(groupid))
                    try:
                        res = await bot.ban_chat_member(
                            groupid,
                            targetUser,
                        )
                    except Exception as ex:
                        if ex == ChatMigrated:
                            logger.info(
                                f"Found chat id changed. Starting to update database."
                            )
                            new_chat_id = ex.new_chat_id
                            updateGbbGroupLog(new_chat_id, groupname)
                        else:
                            expcept_msg = (
                                f"An exception occured when executing gbb command in chat: {chat.id}"
                                f"Exception: {ex}"
                            )
                            logger.warning(expcept_msg)
                            await update.message.reply_html(expcept_msg)

                message = f"User {targetUser} has been global banned."
            else:
                logger.warning(
                    f"User: {user.full_name}({user.id}) is trying to trigger requests."
                )
                message = "You are not permit to do that. Your action will be recorded."
        else:
            message = f"No uid provided. Please check again!"

        await update.message.reply_html(message)

    @staticmethod
    async def addGlobalBanGroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat
        bot = context.bot
        if checkIsVIP(user.id):
            logger.info(
                f"Admin {user.full_name}({user.id}) is trying to add a group to gbb target."
            )

            try:
                createGbbGroupLog(chat.title, chat.id)
                message = "A new gbb target recorded."
            except Exception as ex:
                message = f"An error occur: {ex}"

        else:
            logger.warning(
                f"User: {user.full_name}({user.id}) is trying to trigger requests."
            )
            message = "You are not permit to do that. Your action will be recorded."

        await update.message.reply_html(message)


class GbbRequestCommand:
    @staticmethod
    @HQOnly
    async def showRemainRequests(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        user = update.effective_user
        if checkIsAdmin(user.id):
            logger.info(
                f"Admin: {user.full_name}({user.id}) request the list of remaining requests."
            )
            remainRequestDF = fetchRemainRequest()

            if remainRequestDF.empty:
                await update.message.reply_text(
                    "No pending request exists.",
                )
            else:
                recordList = remainRequestDF.to_dict("records")
                message_context = []
                for _dict in recordList:
                    user_submit = User(
                        _dict["requestUser"], _dict["requestUserName"], False
                    )

                    _message_context = rf"▪RequstID: <pre>{_dict['requestID']}</pre>, 👤Submitee: {user_submit.mention_html()}"

                    message_context.append(_message_context)

                message_context.append(
                    rf"Use <pre>/showRequest</pre> command with request ID to get detail information."
                )
                message = "\n======\n".join(message_context)
                await update.message.reply_html(
                    message,
                )
        else:
            logger.warning(
                f"User: {user.full_name}({user.id}) is trying to access the list of remaining requests."
            )
            await update.message.reply_html("You are not permit to do this.")

    @staticmethod
    @NotPrivate
    async def report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        HQIndex = getHQIndex()
        bot = context.bot
        replied_message = update.message.reply_to_message
        replied_user = replied_message.from_user
        sender = update.effective_user
        chat = update.effective_chat

        if replied_message is not None and context.args != []:
            logger.info(
                f"User: {sender.first_name}({sender.id}) has reported a GBB request in chat: {chat.full_name}({chat.id})."
            )
            comment = "_".join(context.args)
            mesesage = (
                rf"User: {sender.mention_html()} has reported a GBB reuqest in {chat.mention_html()}."
                "\n"
                rf"Reported user: {replied_user.mention_html()}(<pre>{replied_user.id}</pre>)"
                "\n"
                rf"Message link: {replied_message.link}"
                f"\nComment: {comment}."
            )

            bot_reply = await update.message.reply_text(
                "The message has been reported."
            )

            keyboard = [
                [
                    InlineKeyboardButton(
                        "Done",
                        callback_data=f"processed_{chat.id}_{bot_reply.message_id}",
                    ),
                    InlineKeyboardButton(
                        "Reject",
                        callback_data=f"rejected_{chat.id}_{bot_reply.message_id}",
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

    @staticmethod
    @HQOnly
    async def showRequest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        if context.args != []:
            ticketID = context.args[0]
            remainRequestDF = fetchRemainRequest()

            desiredRequest = remainRequestDF.query(f"requestID == @ticketID")

            _dict = desiredRequest.to_dict("records")[0]

            user_submit = User(_dict["requestUser"], _dict["requestUserName"], False)

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
                "Cannot search more than one request at the same time. Please check again.",
            )
        else:
            await update.message.reply_html(
                "No argument found. Abort!",
            )

    @staticmethod
    @PrivateOnly
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Send a message when the command /start is issued."""
        user = update.message.from_user
        chat = update.effective_chat

        if chat.id < 0:
            start_message = (
                rf"Hi {user.mention_html()}! "
                "I am a bot that can help you to submit a gbb request to administrators.\n"
                "Please send me a private message for a submission.\n"
                "Or you may use <pre>/report</pre> with a reason to report a message."
            )
        else:
            start_message = (
                rf"Hi {user.mention_html()}! "
                "I am a bot that can help you to submit a gbb request to administrators.\n"
                "Use <a>/submit</a> to submit a ticket."
            )
        await update.message.reply_html(start_message)

    @staticmethod
    @PrivateOnly
    async def submit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Starts the conversation and asks the user about their requests."""
        ticketID = secrets.token_hex(8)

        user = update.message.from_user
        chat = update.effective_chat

        logger.info(
            f"User: {user.first_name}({user.id}) submit a new ticket with ID: {ticketID}"
        )

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


class UtilityCommand:
    @staticmethod
    async def checkUserID(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        replied_message = update.message.reply_to_message

        if replied_message is not None:
            replied_user = replied_message.from_user
            message = rf"Target User ID: <pre>{replied_user.id}</pre>"
        else:
            user = update.effective_user
            message = rf"Your User ID: <pre>{user.id}</pre>"

        await update.message.reply_html(message)

    @staticmethod
    async def checkChatType(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        chat = update.effective_chat
        message = f"Chat type: {chat.type}"
        await update.message.reply_html(message)

    @staticmethod
    @HQOnly
    async def isAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        replied_message = update.message.reply_to_message
        replied_user = replied_message.from_user

        _isAdmin = checkIsAdmin(replied_user.id)

        keyStone = " a " if _isAdmin else " not a "
        message = rf"User: {replied_user.mention_html()} is{keyStone}administrator."

        await update.message.reply_html(message)

    @staticmethod
    @HQOnly
    async def setAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        replied_message = update.message.reply_to_message
        replied_user = replied_message.from_user
        sender = update.effective_user

        if context.args != []:
            vipOption = context.args[0]

            if vipOption in ["VIP", "GENERAL"]:
                if checkIsVIP(sender.id):
                    logger.info(
                        f"VIP: {sender.full_name}({sender.id}) is trying to grant the permission to {replied_user.full_name}({replied_user.id})."
                    )
                    isVIP = True if vipOption == "VIP" else False
                    createAdminLog(replied_user.id, isVIP)
                    message = rf"User: {replied_user.mention_html()} has been configured as a administrator."
                    logger.info(
                        f"VIP: {sender.full_name}({sender.id}) has granted the permission to {replied_user.full_name}({replied_user.id})."
                    )
                else:
                    logger.warning(
                        f"User: {sender.full_name}({sender.id}) is trying to grant the permission to {replied_user.full_name}({replied_user.id})."
                    )
                    message = "You are not permit to do this."
            else:
                logger.warning(
                    f"User: {sender.full_name}({sender.id}) is trying to grant the permission to {replied_user.full_name}({replied_user.id})."
                )
                message = "No valid option provided. Please check again!"
        else:
            message = f"No option provided. Please check again!"

        await update.message.reply_html(message)

    @staticmethod
    @HQOnly
    async def revokeAdmin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        replied_message = update.message.reply_to_message
        replied_user = replied_message.from_user
        sender = update.effective_user

        if checkIsVIP(sender.id) and not checkIsOwner(replied_user.id):
            try:
                logger.warning(
                    f"Admin: {sender.full_name}({sender.id}) is trying to revoke the permission of {replied_user.full_name}({replied_user.id})."
                )
                deleteAdminLog(replied_user.id)
                message = rf"User: {replied_user.mention_html()} has been revoked."
            except Exception as e:
                logger.warning(
                    f"An error occured when admin: {sender.full_name}({sender.id}) is trying to revoke the permission of {replied_user.full_name}({replied_user.id})."
                )
                message = f"An error occured: {e}."
        elif checkIsOwner(replied_user.id):
            logger.warning(
                f"User: {sender.full_name}({sender.id}) is trying to revoke the permission of {replied_user.full_name}({replied_user.id})."
            )
            message = "Owner is not able to revoke. Your action has been recorded."
        else:
            message = "You are not permit to do this."

        await update.message.reply_html(message)

    @staticmethod
    async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user = update.effective_user
        chat = update.effective_chat
        HQIndex = getHQIndex()
        if (checkIsAdmin(user.id) or checkIsVIP(sender.id)) and chat.id == HQIndex:
            help_msg = (
                rf"<pre>/setAdmin</pre>: Available for VIP, can assign someone as an administrator."
                + "\n"
                rf"<pre>/revokeAdmin</pre>: Available for VIP, can revoke someone's administrator permission."
                + "\n"
                rf"<pre>/isAdmin</pre>: Available for everyone, can check someone's administrator permission."
                + "\n"
                rf"<pre>/setHeadquarter</pre>: Available for VIP, set a chat as the headquarter of this bot. (Can only set one chat as the HQ at the same time.)"
                + "\n"
                rf"<pre>/showRemainRequests</pre>: Available for admin, can show a list of requests that have not been processed."
                + "\n"
                rf"<pre>/showRequest</pre>: Available for admin, can check the information of the specific request. A positional argument in need."
                + "\n"
            )
        elif chat.type == "private":
            help_msg = (
                rf"Use <pre>/submit</pre> command to start a submission." + "\n"
                rf"Use <pre>/cancel</pre> command to interrupt a submission." + "\n"
            )
        elif chat.type != "private" and chat.id != HQIndex:
            help_msg = (
                rf"Use <pre>/report</pre> with reason to report a message. A report without reason will not be proceed."
                + "\n"
            )
        await update.message.reply_html(help_msg)


class VIPCommand:
    @staticmethod
    async def setHeadquarter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Set the headquarter that the request ticket to broadcast."""

        chat = update.effective_chat
        user = update.effective_user

        if checkIsVIP(user.id):
            try:
                logger.warning(
                    f"Admin: {user.full_name}({user.id}) is trying to change the HQ."
                )
                setHQIndex(chat.id)
                await update.message.reply_html("Complete!")
                logger.warning(
                    f"The HQ group has been changed by admin: {user.full_name}({user.id})."
                )

            except Exception as e:
                await update.message.reply_html(f"An error occured: {e}.")
                log_message = (
                    f"An error occured when admin: {user.full_name}({user.id}) is trying to change the HQ.\n"
                    f"Exception: {e}"
                )
                logger.warning(log_message)

        else:
            logger.info(
                f"User: {user.first_name}({user.id}) is trying to change the HQ."
            )
            await update.message.reply_html("You are not permit to do this.")
