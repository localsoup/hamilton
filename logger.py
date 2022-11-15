import logging
from pythonjsonlogger import jsonlogger
import datetime


# Set the logging level to one of the following:
    # NOTSET = 0
    # DEBUG = 10
    # INFO = 20
    # WARN = 30
    # ERROR = 40
    # CRITICAL = 50
LOG_LEVEL = 10


# Configure the format of JSON logs 
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            # this doesn't use record.created, so it is slightly off
            now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
        if log_record.get('level'
            ):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname


# Log as JSON to a local file
logHandler = logging.FileHandler("localsoup.log")
formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
logHandler.setFormatter(formatter)

# Create a logger for data-related events, e.g. no matching data from website
logger = logging.getLogger(__name__)
logger.addHandler(logHandler)
logger.setLevel(LOG_LEVEL)

# Create a logger for HTTP events, e.g. 403 or 500 errors
httpLogger = logging.getLogger('urllib3')
httpLogger.addHandler(logHandler)
httpLogger.setLevel(LOG_LEVEL)