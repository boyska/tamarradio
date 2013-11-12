import logging

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"


def formatter_message(message, use_color=True):
    if use_color:
        message = message.replace("$RESET", RESET_SEQ).\
            replace("$BOLD", BOLD_SEQ)
    else:
        message = message.replace("$RESET", "").replace("$BOLD", "")
    return message


COLORS = {
    'WARNING': YELLOW,
    'INFO': WHITE,
    'DEBUG': BLUE,
    'CRITICAL': YELLOW,
    'ERROR': RED
}


class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, use_color=True):
        logging.Formatter.__init__(self, msg, '%M:%S')
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            levelname_color = COLOR_SEQ % (30 + COLORS[levelname]) + \
                levelname[0] + RESET_SEQ
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)


# Custom logger class with multiple destinations
class ColoredLogger(logging.Logger):
    FORMAT = "[%(asctime)s][$BOLD%(name)-12s$RESET %(levelname)s] " + \
             "%(message)s ($BOLD%(filename)s$RESET:%(lineno)d)"
    COLOR_FORMAT = formatter_message(FORMAT, True)
    default_level = logging.DEBUG

    def __init__(self, name):
        logging.Logger.__init__(self, name, self.default_level)

        color_formatter = ColoredFormatter(self.COLOR_FORMAT)

        console = logging.StreamHandler()
        console.setFormatter(color_formatter)

        self.addHandler(console)


def cls_logger(f):
    def new_init(self, *args, **kwargs):
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(ColoredLogger.default_level)

        if not self.log.handlers:
            color_formatter = ColoredFormatter(ColoredLogger.COLOR_FORMAT)
            console = logging.StreamHandler()
            console.setFormatter(color_formatter)
            self.log.addHandler(console)

        f(self, *args, **kwargs)

    return new_init
