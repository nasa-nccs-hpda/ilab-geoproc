# Core implementation of gee class for the innovation lab
# Download imagery from gee and make it in processable fashion
import ee
import re

class AutoGEE(self):

    def __init__(
            self,
            logger=None,
            gee_account: str = None,
            gee_key: str = None
        ):

        # set GEE session if auth is given
        self.init_gee(gee_account, gee_key)

    # -------------------------------------------------------------------------
    # init_gee()
    # -------------------------------------------------------------------------
    def init_gee(self, gee_account: str, gee_key: str) -> None:
        """__summary__: Initialize GEE authentication
        """
        # validate that gee_account has email format
        assert re.search(r'[\w.]+\@[\w.]+', gee_account), \
            f"gee_account must be a valid email, {gee_account}"

        # validation that gee_key is stored in json file
        assert gee_key.endswith('.json'), \
            f"gee_key needs to be a file that ends in .json, {gee_key}"

        # initialize authentication
        if not ee.data._credentials:
            credentials = ee.ServiceAccountCredentials(gee_account, gee_key)
            ee.Initialize(credentials)
            logging.info('GEE authentication set.')
        return
