import json
import logging

from aiohttp.client import ClientSession
from utils import get_url, post_url, post_jurl

###################################
logging.basicConfig(filename='lnaddress.log', level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logging.getLogger("lnaddress").setLevel(level=logging.WARNING)
logger = logging.getLogger(__name__)
###################################

class LNAddress:
    """
    Async Methods for Payment to a LN Address w/LNBits API
    """
    def __init__(self, config, session: ClientSession = None):
        self._session = session
        self._inv_key = config['invoice_key']
        self._admin_key = config['admin_key']
        self.base_url = config['base_url']

    
    def invoice_headers(self):
        """
        invoice key  
        """
        data = {"X-Api-Key": self._inv_key, "Content-type": "application/json"}
        return data


    def admin_headers(self):
        """
        admin key
        """
        data = {"X-Api-Key": self._admin_key, "Content-type": "application/json"}
        return data


    def headers(self):
        """
        standard headers
        """
        data = {"Content-type": "text/html; charset=UTF-8"}
        return data

    def get_payurl(self, email: str):
        """
        Construct Lnurlp link from email address provided. 
        """

        try:
            parts = email.split('@')
            domain = parts[1]
            username = parts[0]
            # assume https
            transform_url = "https://" + domain + "/.well-known/lnurlp/" + username
            logging.info("Transformed URL:" + transform_url)
            return transform_url
        except Exception as e: 
            logging.error("Exception, possibly malformed LN Address: " + e)
            return {'status' : 'error', 'msg' : 'Possibly a malformed LN Address'}


    async def get_bolt11(self, email: str, amount: int): 
        """
            get Bolt11 Invoice from Lightning Address (variable named email here)

            fail state
            {'reason': 'Amount 100 is smaller than minimum 100000.', 'status': 'ERROR'}

            success state
            {'pr': 'lnbc1......azgfe0', 
            'routes': [], 'successAction': {'description': 'Thanks love for the lightning!', 
            'tag': 'url', 'url': 'https:/.......'}}
        """
        try: 
            purl = self.get_payurl(email)
            json_content = await get_url(session=self._session, path=purl, headers=self.headers())
            datablock = json.loads(json_content)

            lnurlpay = datablock["callback"]
            min_amount = datablock["minSendable"]

            payquery = lnurlpay + "?amount=" + str(min_amount)
            if amount is not None:
                if int(amount*1000) > int(min_amount):
                    payquery = lnurlpay + "?amount=" + str(amount*1000)
            
            logging.info("amount: " + str(amount))
            logging.info("payquery: " + str(payquery))
        
            # TODO: check if URL is legit, else return error
            # get bech32-serialized lightning invoice
            ln_res =  await get_url(session=self._session, path=payquery, headers=self.headers())
            pr_dict = json.loads(ln_res)

            # check keys returned for status
            if 'status' in pr_dict: 
                reason = pr_dict['reason']
                return reason
            elif 'pr' in pr_dict: 
                bolt11 = pr_dict['pr']
                return bolt11
            
        except Exception as e: 
            logging.error("in get bolt11 : "  + str(e))
            return {'status': 'error', 'msg': 'Cannot make a Bolt11, are you sure the address is valid?'}


    async def get_payhash(self, bolt11):
        """
        get payment hash from bolt11 - use json on post request
        """
        try:
            decode_url = self.base_url + "/decode"
            payload = {'data': bolt11}
            decoded =  await post_jurl(session=self._session, path=decode_url, json=payload, headers=self.invoice_headers())
            # logging.info(decoded)
            if 'payment_hash' in decoded:
                payhash = decoded['payment_hash']
                logging.info('payment hash: ' + payhash)
                return payhash
        except Exception as e:
            logging.error('Exception in get_payhash() ', str(e))
            return e


    async def check_invoice(self, payhash):
        """
        check payment hash from decoded BOLT11 - works
        """
        try:
            payhashurl = self.base_url + "/" + str(payhash)
            res =  await get_url(session=self._session, path=payhashurl, headers=self.invoice_headers())
            output = json.loads(res)
            # logging.info("check invoice response: " + output)
            pay_status = output['paid']
            pay_preimage = output['preimage']
            return pay_status, pay_preimage
        except Exception as e:
            logging.error('Exception in get_paystatus() ', str(e))
            return e


    async def pay_invoice(self, bolt11): 
        """
        pay bolt11 invoice

        error message:
        {'message': '{"error":"self-payments not allowed","code":2,"message":"self-payments not allowed","details":[]}'}        
        """
        try:
            data = {"out": True, "bolt11": bolt11}
            body = json.dumps(data)
            logging.info(f"body: {body}")
            res =  await post_url(session=self._session, path=self.base_url, body=body, headers=self.admin_headers())
            logging.info(res)
            return res
        except Exception as e: 
            logging.error('Exception in pay_invoices(): ', e)
            return e