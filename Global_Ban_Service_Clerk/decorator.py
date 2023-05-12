import logging
from dotenv import dotenv_values
from .utils import getHQIndex, checkGbbConfig, checkIsAdmin, checkIsVIP

logger = logging.getLogger(__name__)

def checkAdmin(func):
    async def wraps(*args, **kargs):
        user = args[0].effective_user
        
        if checkIsAdmin(user.id):
            logger.info(
                f"Admin {user.full_name}({user.id}) is trying to execute function: {func.__name__}."
            )
            return await func(*args, **kargs)
        else:
            logger.warning(
                f"User {user.full_name}({user.id}) is trying to execute admin only function: {func.__name__}."
            )
            return await args[0].message.reply_text(
                "You are not permit to do that. Your action will be recorded."
            )
    return wraps

def checkVIP(func):
    async def wraps(*args, **kargs):
        user = args[0].effective_user
        
        if checkIsVIP(user.id):
            logger.info(
                f"VIP {user.full_name}({user.id}) is trying to execute function: {func.__name__}."
            )
            return await func(*args, **kargs)
        else:
            logger.warning(
                f"User {user.full_name}({user.id}) is trying to execute VIP only function: {func.__name__}."
            )
            return await args[0].message.reply_text(
                "You are not permit to do that. Your action will be recorded."
            )
    return wraps

def checkReplied(func):
    async def wraps(*args, **kargs):
        replied_message = args[0].message.reply_to_message
        
        if replied_message is not None:
            return await func(*args, **kargs)
        else:
            return await args[0].message.reply_text(
                "This function only works when replying to a specific message. "
                "Please check again."
            )
    return wraps

def HQOnly(func):
    async def wraps(*args, **kargs):
        chat = args[0].effective_chat
        HQIndex = getHQIndex()
        # replied_message = args[0].message.reply_to_message

        if chat.id == HQIndex:
            return await func(*args, **kargs)
        elif chat.id == 9999999999999999:
            return await args[0].message.reply_text(
                "No HQ Chat ID set. Set HQ Index to run."
            )
        else:
            return await args[0].message.reply_text(
                "This function can only operate in Headquarter."
            )

    return wraps


def NotPrivate(func):
    async def wraps(*args, **kargs):
        chat = args[0].effective_chat
        HQIndex = getHQIndex()
        # replied_message = args[0].message.reply_to_message

        if chat.id != HQIndex and chat.type != "private":
            return await func(*args, **kargs)
        else:
            return await args[0].message.reply_text(
                "This function cannot operate in private chat."
            )

    return wraps


def PrivateOnly(func):
    async def wraps(*args, **kargs):
        chat = args[0].effective_chat
        HQIndex = getHQIndex()

        if chat.id != HQIndex and chat.type == "private":
            return await func(*args, **kargs)
        else:
            return await args[0].message.reply_text(
                "This function cannot operate in private chat."
            )

    return wraps


def GbbFilter(func):
    async def wraps(*args, **kargs):
        if checkGbbConfig():
            return await func(*args, **kargs)
        else:
            pass
    return wraps

def checkArgumentExist(func):
    async def wraps(*args, **kargs):
        if args[1].args != []:
            return await func(*args, **kargs)
        else:
            return await args[0].message.reply_text(
                "This function must operate with arguments. "
                "Please check again."
            )
    return wraps


    