import logging, os, time, socket

class ILABLogger:
    logger = None

    @classmethod
    def getLogger(cls, name:str = "ilab" ):
        if cls.logger is None:
            scratch_dir = os.environ["ILSCRATCH"]
            LOG_DIR = os.path.join( scratch_dir, "logs" )
            if not os.path.exists(LOG_DIR):  os.makedirs(LOG_DIR)
            timestamp = time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())
            cls.logger = logging.getLogger( name )
            cls.logger.setLevel(logging.DEBUG)
            fh = logging.FileHandler("{}/{}-{}-{}.log".format(LOG_DIR, name, socket.gethostname(), timestamp))
            fh.setLevel(logging.DEBUG)
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            formatter = logging.Formatter( name + '-%(asctime)s-%(levelname)s: %(message)s' )
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)
            cls.logger.addHandler(fh)
            cls.logger.addHandler(ch)
        return cls.logger