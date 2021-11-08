import os 
import asyncio
from aiohttp.client import ClientSession
from ln_address import LNAddress
import logging

###################################
logging.basicConfig(filename='test_lnaddress.log', level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logging.getLogger("testlnaddress").setLevel(level=logging.WARNING)
logger = logging.getLogger(__name__)
###################################


async def main():
    email = 'bitkarrot@bitcoin.org.hk'
    amount = 150 # amount in sats
    
    # email = 'foo@example.com' # non working ln address
    # amount = None 
    
    # Get environment variables
    invoice_key = os.getenv('INVOICE_KEY')
    admin_key = os.getenv('ADMIN_KEY')
    base_url =  os.getenv('BASE_URL') 

    config = { 'invoice_key': invoice_key, 
                'admin_key': admin_key, 
                'base_url': base_url }

    async with ClientSession() as session:
        logging.info("in ClientSession")
        lnaddy = LNAddress(config, session)
        bolt11 = await lnaddy.get_bolt11(email, amount)
        logging.info(bolt11)
 
        payhash = await lnaddy.get_payhash(bolt11)
        print(payhash)

        status, image = await lnaddy.check_invoice(payhash)
        print('paid status:', status, " image : ", image)

        # pay invoice 
        result = await lnaddy.pay_invoice(bolt11)
        if result is dict:
            print('pay invoice status: ', result)
            payment_hash = result['payment_hash']
            # check payment hash status -
            status, image = await lnaddy.check_invoice(payment_hash)
            print('paid status:', status, " image : ", image)
        

loop = asyncio.get_event_loop()
loop.run_until_complete(main())


