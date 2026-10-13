
import logging


grey = "\x1b[30m"
green = "\x1b[1;32m"
yellow = "\x1b[33;20m"
red = "\x1b[31;20m"
bold_red = "\x1b[31;1m"
blue = "\x1b[1;34m"
# purple = "\x1b[1;35m"
reset = "\x1b[0m"


class ConsoleFormatter(logging.Formatter):
    timeFormat = grey + "[%(asctime)s]" + reset + " - "
    messageFormat = ": " + "%(message)s"

    debugFormat = timeFormat + blue + "%(levelname)s" + reset + messageFormat
    infoFormat = timeFormat + green + "%(levelname)s" + reset + messageFormat
    warningFormat = timeFormat + yellow + \
        "%(levelname)s" + reset + messageFormat
    errorFormat = timeFormat + red + "%(levelname)s" + reset + messageFormat
    criticalFormat = timeFormat + bold_red + \
        "%(levelname)s" + reset + messageFormat

    FORMATS = {
        logging.DEBUG: debugFormat,
        logging.INFO: infoFormat,
        logging.WARNING: warningFormat,
        logging.ERROR: errorFormat,
        logging.CRITICAL: criticalFormat
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        if record.args:
            log_fmt = log_fmt + yellow + " : %(args)s" + reset
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class FileFormatter(logging.Formatter):
    def format(self, record):
        log_fmt = "[%(asctime)s] - %(levelname)s: %(message)s"
        if record.args:
            log_fmt = log_fmt + " : %(args)s"
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


# create logger with 'spam_application'
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


console_level = "DEBUG"
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(ConsoleFormatter())
logger.addHandler(console_handler)

file_handler = logging.FileHandler("./logs/app.log")
file_level = "DEBUG"
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(FileFormatter())
logger.addHandler(file_handler)
