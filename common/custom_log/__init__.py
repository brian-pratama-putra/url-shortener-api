import os
import globalVar

try :
    LOG_NAME = globalVar.LOG_NAME
except :
    LOG_NAME = "SKELETON"
from datetime import datetime as dtlog
from pathlib import Path
from zoneinfo import ZoneInfo

class Logger :
    TZ_JAKARTA = ZoneInfo("Asia/Jakarta")
    def __init__(self):
        self.__logger = ""
        self.createLogger()

    def createLogger(self, logName = LOG_NAME):
        if os.getenv("GAE_ENV") == "standard" :
            from google.cloud import logging_v2
            from google.cloud.logging_v2.resource import Resource
            self.__client = logging_v2.Client()
            self.__logger = self.__client.logger(logName)
            self.__resource = Resource(
                type="gae_app",
                labels={
                    "module_id": os.getenv("GAE_SERVICE"),
                    "project_id": os.getenv("GOOGLE_CLOUD_PROJECT"),
                    "version_id": os.getenv("GAE_VERSION")})
        elif os.getenv("CLOUD_APPS") == "CLOUD_RUN" :
            from google.cloud import logging
            logging_client = logging.Client()
            self.__logger = logging_client.logger(logName)
        else :
            Path(f"{os.getcwd()}/log").mkdir(parents=True, exist_ok=True)
            self.__logger = f"""{os.getcwd()}/log/{dtlog.now(Logger.TZ_JAKARTA).strftime("%Y-%m-%d")}.txt"""

    def __logStruct(self, severity, msg):
        if os.getenv("GAE_ENV") == "standard" :
            self.__logger.log_struct(info={"message": msg}, severity=severity, resource=self.__resource)
        elif os.getenv("CLOUD_APPS") == "CLOUD_RUN" :
            dictParam = f"""{severity} | {dtlog.now(Logger.TZ_JAKARTA).strftime("%Y-%m-%d")} | {dtlog.now(Logger.TZ_JAKARTA).strftime("%H:%M:%S")} | {msg}"""
            self.__logger.log_text(dictParam, severity=severity)
        else :
            fileOpen = open(self.__logger, "a")
            dictParam = f"""{severity} | {dtlog.now(Logger.TZ_JAKARTA).strftime("%Y-%m-%d")} | {dtlog.now(Logger.TZ_JAKARTA).strftime("%H:%M:%S")} | {msg}"""
            fileOpen.write(f"{str(dictParam)}\n")
            fileOpen.close()

    def debug(self, message):
        self.__logStruct(severity="DEBUG", msg=message)

    def info(self, message):
        self.__logStruct(severity="INFO", msg=message)

    def warning(self, message):
        self.__logStruct(severity="WARNING", msg=message)

    def error(self, message):
        self.__logStruct(severity="ERROR", msg=message)

    def critical(self, message):
        self.__logStruct(severity="CRITICAL", msg=message)

    def exception(self, message):
        import traceback
        full_msg = f"{message}\n{traceback.format_exc()}"
        self.__logStruct(severity="ERROR", msg=full_msg)
