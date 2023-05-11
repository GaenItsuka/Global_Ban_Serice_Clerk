from dotenv import dotenv_values
from .utils import getHQIndex, checkGbbConfig


def HQOnly(func):
    async def wraps(*args, **kargs):
        chat = args[0].effective_chat
        HQIndex = getHQIndex()
        replied_message = args[0].message.reply_to_message
        
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
        replied_message = args[0].message.reply_to_message

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