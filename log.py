import logging

SPAM_LEVEL_NUM = logging.DEBUG - 1

def _spamLogMethod(self, message, *args, **kws):
    # Yes, logger takes its '*args' as 'args'.
    if self.isEnabledFor(SPAM_LEVEL_NUM):
        self._log(SPAM_LEVEL_NUM, message, args, **kws)
        pass
    pass

def init(name, verbosity, logFile=None):
    logging.addLevelName(SPAM_LEVEL_NUM, "SPAM")
    logging.Logger.spam = _spamLogMethod
    logger = logging.getLogger(name)
    if verbosity > 1:
        logger.setLevel(SPAM_LEVEL_NUM)
        pass
    elif verbosity > 0:
        logger.setLevel(logging.DEBUG)
        pass
    else:
        logger.setLevel(logging.INFO)
        pass        

    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s:%(funcName)s(): - %(message)s')
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(formatter)
    logger.addHandler(consoleHandler)
    
    if logFile is not None:
        fileHandler = logging.FileHandler(logFile)
        fileHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)

    pass
 
