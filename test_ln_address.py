import json
import os 
import asyncio
from aiohttp.client import ClientSession
from ln_address import LNAddress
import logging

###################################
logging.basicConfig(filename='lnaddress.log', level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logging.getLogger("lnaddress").setLevel(level=logging.WARNING)
logger = logging.getLogger(__name__)
###################################


async def main():
    email = 'bitkarrot@bitcoin.org.hk'
    amount = 150 # amount in sats
    
    email = 'foo@example.com' # non working ln address
    amount = None 
    
    # Get environment variables
    invoice_key = os.getenv('INVOICE_KEY')
    admin_key = os.getenv('ADMIN_KEY')
    base_url =  os.getenv('BASE_URL') 

    config = { 'invoice_key': invoice_key, 
                'admin_key': admin_key, 
                'base_url': base_url }

    try:
        async with ClientSession() as session:
            logging.info("in ClientSession")
            lnaddy = LNAddress(config, session)
            bolt11 = await lnaddy.get_bolt11(email, amount)
            logging.info(bolt11)
    
            payhash = await lnaddy.get_payhash(bolt11)
            logging.info("response from get_payhash: " + str(payhash))
    
            # check payment hash status -
            output = await lnaddy.check_invoice(payhash)
            if 'paid' in output:
                pay_status = output['paid']
                pay_preimage = output['preimage']
                paid_status= 'paid status:'+ str(pay_status)
                img_status = "image: "  + str(pay_preimage)
                logging.info(paid_status)
                logging.info(img_status)
            else: 
                logging.info(output)

            # pay invoice 
            result = await lnaddy.pay_invoice(bolt11)
            logging.info("pay invoice result:")
            logging.info(result)

            # check payment hash status -
            payment_hash = result['payment_hash']
            output = await lnaddy.check_invoice(payment_hash)
            if 'paid' in output:
                pay_status = output['paid']
                pay_preimage = output['preimage']
                paid_status= 'paid status:'+ str(pay_status)
                img_status = "image: "  + str(pay_preimage)
                logging.info(paid_status)
                logging.info(img_status)
            else: 
                logging.info(output)

    except Exception as e:
        logging.error(e)

            
        

loop = asyncio.get_event_loop()
loop.run_until_complete(main())


