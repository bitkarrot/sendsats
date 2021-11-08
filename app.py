from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.responses import RedirectResponse
import uvicorn

from ln_address import LNAddress
from aiohttp.client import ClientSession
from io import BytesIO

import pyqrcode
import os
import logging

###################################
logging.basicConfig(filename='api.log', level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logging.getLogger("app").setLevel(level=logging.WARNING)
logger = logging.getLogger(__name__)
###################################

content = [ 
    " Example Use: <h1>  https://sendsats.to/me@mydomain.com </h1> ", 
    " will return a scannable Lightning QR Code for any valid Lightning Address. <br><br> ",
    " An API for getting QR codes and Bolt11 Invoices from Lightning Addresses. ", 
    " Share anywhere; as a link for tips on a twitter profile, or via messenger apps."]

description = ''.join(content)
title = "sendsats.to"

# Get environment variables if using LNBits as backend
invoice_key = os.getenv('INVOICE_KEY')
admin_key = os.getenv('ADMIN_KEY')
base_url =  os.getenv('BASE_URL') 

config = { 'invoice_key': invoice_key, 
            'admin_key': admin_key, 
            'base_url': base_url }

app = FastAPI(
    title=title,
    description=description,
    version="0.0.1 alpha",
    contact={
        "name": "bitkarrot",
        "url": "http://github.com/bitkarrot/sendsats",
    },
    license_info={
        "name": "MIT License",
        "url": "https://mit-license.org/",
    },
)

async def get_bolt(email, amount):
    """
        get bolt from ln addy email, amount
        returns bolt11
    """
    try: 
        async with ClientSession() as session:
            lnaddy = LNAddress(config, session)
            bolt11 = await lnaddy.get_bolt11(email, amount)
            logging.info(bolt11)
            return bolt11
    except Exception as e: 
        logging.error(e)
        return None


@app.get('/tip/{lightning_address}/amt/{tip_amount}')
async def get_Tip_QR_Code(lightning_address: str, tip_amount: str):
    """
    this endpoint returns a QR PNG image when given a Lightning Address and tip amount.
    example use: /tip/user@domain.com/amt/100
    """

    try:
        logging.info("LN Address", lightning_address, "tip amount: ", tip_amount)
        print("LN Address", lightning_address, "tip amount: ", tip_amount)

        bolt11 = await get_bolt(lightning_address, int(tip_amount))
        qr = pyqrcode.create(bolt11)
        tip_file = '/tmp/qr_tip.png'
        qr.png(tip_file, scale=3, module_color=[0,0,0,128], background=[0xff, 0xff, 0xff])
        return FileResponse(tip_file)
    except Exception as e:
        return { 
            "msg" : "Not a valid tipping Address. Sorry!"
        }


@app.get('/qr/{lightning_address}')
async def get_QR_Code_From_LN_Address(lightning_address: str):
    """
    this endpoint returns a QR PNG image when given a Lightning Address.
    example use: /qr/user@mydomain.com
    """
    try:
        if lightning_address is not None:    
            tip_file = '/tmp/qr_lnaddy.png'
            bolt11 = await get_bolt(lightning_address, None)
            qr = pyqrcode.create(bolt11) 
            qr.png(tip_file, scale=3, module_color=[0,0,0,128], background=[0xff, 0xff, 0xff])
            return FileResponse(tip_file)
        else: 
            return {
                "msg" : "Please send a valid Lightning Address"
            }
    except Exception as e: 
        return { 
            "msg" : "Not a valid Lightning Address. Sorry!"
        }



@app.get('/bolt11/{lightning_address}')
async def get_qr_via_bolt11(lightning_address: str):
    """
    this end point returns a bolt11 Invoice when given a lightning address as parameter
    example use: /bolt11/user@domain.com 
    """
    try:
        if lightning_address is not None:
            bolt11 = await get_bolt(lightning_address, None)
            # TODO >>>>> check if bolt11 is valid
            return {
                "bolt11" : bolt11
            }
        else: 
            return {
                "msg" : "Please send give a lightning address"
            }
    except Exception as e:
        return { 
            "msg" : "Not a valid Lightning Address"
        }


@app.get("/svg/{lightning_address}")
async def get_svg_img_from_LN_address(lightning_address): 
    """
    this endpoint returns image in SVG - XML format  as part of json response
    example use: /svg/user@domain.com
    """
    try: 
        logging.info(lightning_address)
        bolt11 = await get_bolt(lightning_address, None)
        qr = pyqrcode.create(bolt11)
        
        stream = BytesIO()
        qr.svg(stream, scale=3)

        return (
                stream.getvalue(),
                200,
                {
                    "Content-Type": "image/svg+xml",
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
        )
    except Exception as e: 
        logging.error(e)
        return { 
            "msg" : "Not a valid Lightning Address"
        }


@app.get("/{lightning_address}")
async def forward_to_QR_Endpoint(lightning_address):
    """
    this endpoint forwards the lightning address to the /qr endpoint
    example use: /user@domain.com
    """
    try:
        if '@' in lightning_address:
            return await get_QR_Code_From_LN_Address(lightning_address)
    except Exception as e:
        logging.error(e) 
#        return RedirectResponse("/docs")
        return { 
            "msg" : "Not a valid Lightning Address"
        }


@app.get("/")
async def API_Docs():
    """
    Redirects queries from top level domain to API docs (this page)
    """
    return RedirectResponse("/docs")





# for local testing
if __name__ == "__main__":
  uvicorn.run("app:app", host="localhost", port=3000, reload=True)