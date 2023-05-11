import os
import sys
import sqlite3
import toml
import logging
import pandas as pd

from functools import partial
from datetime import datetime
from secrets import token_hex

logger = logging.getLogger(__name__)

############################################################
#
#               Bacis Utilities
#
############################################################


def preflightCheck(ownerID):
    chkList = [
        "gbb.db",
        "GbbRequestDB.db",
        "Admin.db",
        "config/config.toml",
    ]
    partialCreateAdminDB = partial(createAdminDB, ownerID=ownerID)
    funcList = [
        createGbbGroupTable,
        createRequestLogTable,
        partialCreateAdminDB,
        createConfig,
    ]

    chkDescription = [
        "Creating DB for Gbb Grouos",
        "Creating DB for request logs.",
        "Creating DB for admin.",
        "Creating toml file for basic config.",
    ]
    for check, func, description in zip(chkList, funcList, chkDescription):
        if not os.path.exists(check):
            logger.info(description)
            func()
        else:
            while True:
                response = input(f"{check} already exists, skip? (y/n) ")
                if response not in ["y", "n"]:
                    print("Please input 'y' or 'n'.")
                    continue
                elif response == "y":
                    break
                elif response == "n":
                    sys.exit(0)


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
#               Global Ban record utilities
#
############################################################


def createGbbGroupTable():
    conn, cursor = createConnection("gbb.db")
    response = cursor.execute(
        """CREATE TABLE IF NOT EXISTS GbbGroup (
            groupname text,
            groupid text
        );
        """
    )
    result = response.fetchall()
    return result


def createGbbGroupLog(
    groupName: str,
    groupID: str,
):
    conn, cursor = createConnection("gbb.db")

    response = cursor.execute(
        f"""INSERT INTO GbbGroup (
            groupname,
            groupid
        )
        VALUES (
            "{groupName}",
            "{groupID}"
        );
        """
    )
    conn.commit()
    conn.close()


def getGbbGroupLog():
    conn, cursor = createConnection("gbb.db")
    df = pd.read_sql(f"SELECT * FROM GbbGroup", conn)
    return df


def updateGbbGroupLog(new_id, groupname):
    conn, cursor = createConnection("gbb.db")
    response = cursor.execute(
        f"""UPDATE GbbGroup
        SET groupid = "{new_id}"
        WHERE groupname = "{groupname}";
        """
    )


def removeGbbGroupLog(chat_id):
    conn, cursor = createConnection("gbb.db")
    response = cursor.execute(
        f"""DELETE FROM GbbGroup
        WHERE groupid = "{chat_id}";
        """
    )


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
            requestEvidencePhoto text,
            isEvidenceHasPhoto bool,
            processed bool,
            result text,
            handler text
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
    requestEvidencePhoto: str = None,
    isEvidenceHasPhoto: bool = False,
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
            requestEvidencePhoto,
            isEvidenceHasPhoto,
            processed,
            result,
            handler
        ) 
        VALUES (
            "{ticketID}",
            "{ticketMessageID}",
            "{datetime.now()}",
            "{ticketUser}",
            "{ticketUserName}",
            "{ticketType}",
            "{requestEvidence}",
            "{requestEvidence}",
            {isEvidenceHasPhoto},
            False,
            "None",
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
    requestEvidencePhoto: str = None,
    isEvidenceHasPhoto: bool = None,
    handler: str = None,
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
            SET requestEvidence = "{requestEvidence}"
            WHERE requestID = "{ticketID}"
            """
        )
    elif requestEvidencePhoto is not None:
        response = cursor.execute(
            f"""UPDATE GbbRequest
            SET requestEvidencePhoto = "{requestEvidencePhoto}",
                isEvidenceHasPhoto = True
            WHERE requestID = "{ticketID}"
            """
        )
    elif handler is not None:
        response = cursor.execute(
            f"""UPDATE GbbRequest
            SET handler = "{handler}",
                processed = True
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


def createConfig():
    os.makedirs("./config")
    cfg = """
    [Headquarter]
    chatID = 99999999999999
    """
    parsedCfg = toml.loads(cfg)
    with open("config/config.toml", "w") as file:
        savedCfg = toml.dump(parsedCfg, file)


def setHQIndex(chatID):
    cfg = toml.load("config/config.toml")
    cfg["Headquarter"]["chatID"] = chatID
    with open("config/config.toml", "w") as file:
        savedCfg = toml.dump(cfg, file)


def getHQIndex():
    cfg = toml.load("config/config.toml")
    return cfg["Headquarter"]["chatID"]


############################################################
#
#               Trust user utilities
#
############################################################


def createAdminDB(ownerID=9999999999):
    conn, cursor = createConnection(DBName="Admin.db")
    response = cursor.execute(
        """CREATE TABLE IF NOT EXISTS Admin (
            UID text,
            CLASS text,
            IsOWNER bool,
            VIP bool,
            UNIQUE(UID)
            );
        """
    )
    cursor.execute(
        f"""INSERT INTO Admin (UID, CLASS, IsOWNER, VIP) 
        VALUES ("{ownerID}", "admin", {True}, {True});
        """
    )
    # result = response.fetchall()
    conn.commit()
    conn.close()


def createAdminLog(UID, isVIP):
    conn, cursor = createConnection(DBName="Admin.db")
    response = cursor.execute(
        f"""INSERT INTO Admin (UID, CLASS, IsOWNER, VIP) 
        VALUES ("{UID}", "admin", {False}, {isVIP});
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
    response = cursor.execute("SELECT UID FROM Admin WHERE CLASS = 'admin';").fetchall()
    adminList = [record_tuple[0] for record_tuple in response]

    result = str(UID) in adminList
    return result


def checkIsVIP(UID):
    conn, cursor = createConnection(DBName="Admin.db")
    response = cursor.execute(
        "SELECT UID FROM Admin WHERE CLASS = 'admin' AND VIP = True;"
    ).fetchall()
    vipList = [record_tuple[0] for record_tuple in response]

    result = str(UID) in vipList
    return result


def checkIsOwner(UID):
    conn, cursor = createConnection(DBName="Admin.db")
    response = cursor.execute("SELECT UID FROM Admin WHERE CLASS = 'owner';").fetchall()
    onwer = response[0]
    isOwner = int(onwer) == UID
    return isOwner
