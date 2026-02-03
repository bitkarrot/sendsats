from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, Form, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import uvicorn

from ln_address import LNAddress
from aiohttp.client import ClientSession
from io import BytesIO

import pyqrcode
import os

import logging
###################################
# Serverless-compatible logging (stdout instead of file)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logging.getLogger("app").setLevel(level=logging.WARNING)
logger = logging.getLogger(__name__)
###################################

content = [
    " <h2> Lightning Address QR Code API </h2> ",
    " Generate scannable QR codes and BOLT11 invoices from Lightning Addresses. <br><br> ",
    " <h3> Quick Start </h3> ",
    " <ul> ",
    " <li> <b> Clean QR page: </b> <code> https://sendsats.to/bitkarrot@nostr.com?amount=10000&memo=forservices </code> </li> ",
    " <li> <b> Tip page: </b> <code> https://sendsats.to/tip/bitkarrot@nostr.com/amt/100 </code> </li> ",
    " <li> <b> QR image: </b> <code> https://sendsats.to/qr/bitkarrot@nostr.com </code> </li> ",
    " <li> <b> JSON invoice: </b> <code> https://sendsats.to/bolt11/bitkarrot@nostr.com/amt/100 </code> </li> ",
    " </ul> ",
    " Share anywhere; as a link for tips on a twitter profile, or via messenger apps. ",
    " Source at <b> <a href=\"https://github.com/bitkarrot/sendsats\"> https://github.com/bitkarrot/sendsats </a> </b>"
]

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

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5000",
    "https://sendsats.to",
    "http://sendsats.to"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import pathlib
# Get the project root directory (works both locally and on Vercel)
BASE_DIR = pathlib.Path(__file__).parent
static_dir = BASE_DIR / "static"
templates_dir = BASE_DIR / "templates"

app.mount("/static", StaticFiles(directory=str(static_dir)), name='static')
templates = Jinja2Templates(directory=str(templates_dir))


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



async def get_qr_page_data(lightning_address, amount):
        print("inside get_qr_page_data amount: " + str(amount))
        if lightning_address is not None:
            async with ClientSession() as session:
                lnaddy = LNAddress(config, session)
                callback_data = await lnaddy.callback_data(lightning_address)
                #print(callback_data)
                # need to update option for None as user specified value
                url = lnaddy.get_payurl(lightning_address)
                #print("url: " + str(url))
                bolt11 = await lnaddy.get_bolt11(lightning_address, amount)
                #print("bolt11: " + str(bolt11))

                # Create QR code with lightning: prefix and uppercase bolt11
                lightning_uri = "lightning:" + bolt11
                qr = pyqrcode.create(lightning_uri)

                # Generate PNG base64 for more reliable scanning
                qr_png_base64 = await get_png_base64_from_qr(qr)

                # default colors for svg are black and white
                svgdata = await get_svg_from_qr(qr, None, None)
                svgxml = svgdata[0].decode('UTF-8')
                # Get the SVG content properly (skip XML declaration)
                lines = svgxml.split('\n')
                svgxml_image = lines[1] if len(lines) > 1 else svgxml
                # Remove width and height attributes from SVG for proper CSS sizing
                svgxml_image = svgxml_image.replace(' height="315"', '').replace(' width="315"', '')
                svgxml_image = svgxml_image.replace(' height="105"', '').replace(' width="105"', '')
                min_send = str(int(callback_data['minSendable']/1000))
                max_send = str(int(callback_data['maxSendable']/1000))
                data = {"url": url, "bolt11": bolt11.lower(),
                        "min": min_send, "max": max_send,
                        "qr": svgxml_image, "qr_png": qr_png_base64,
                        "callback_data": callback_data,
                        "pr_dict": lnaddy.pr_dict, "amount": amount}
                return data



@app.get("/")
async def index_get(request: Request):
    result = "Fill in above to get a QR code"
    lightning_address = "bitkarrot@nostr.com"
    amount = "100"
    return templates.TemplateResponse('index.html', context={'request': request,
                                                              'result': result,
                                                              'lnaddress': lightning_address,
                                                              'amount': amount})


@app.post('/')
async def index_post(request: Request, amount: int = Form(...), lnaddress: str = Form(...)):
    # result = {"amount" : amount , "lnaddress" : lnaddress}
    try:
        #print("Amount posted : " + str(amount))
        if type(amount) is not int:
            raise Exception("amount must be an integer")

        if '@' in lnaddress:
            # print("inside post /")
            data = await get_qr_page_data(lnaddress, amount)

            return templates.TemplateResponse('sats.html',
                                    context={'request': request,
                                            'lnaddress': lnaddress,
                                            'bolt11': data['bolt11'],
                                            'url': data['url'],
                                            'min_send': data['min'],
                                            'max_send': data['max'],
                                            'callback': data['callback_data'],
                                            'amount': data['amount'],
                                            'pr_dict': data['pr_dict'],
                                            'qrdata': data['qr']})
        else:
            return [{
                "msg" : "Please send a valid Lightning Address",
            }]

    except Exception as e:
        logging.error(e)
        print(e)
        return [{
            "msg" : "Not a valid Lightning Address",
            "error": "Error {0}".format(str(e))
        }]
    # return templates.TemplateResponse('sats.html', context={'request': request,
    #                                                          'result': result,
    #                                                           'amount': amount,
    #                                                           'lnaddress': lnaddress})




@app.get('/tip/{lightning_address}/amt/{tip_amount}')
async def get_Tip_QR_Code(lightning_address: str, tip_amount: str, request: Request):
    """
    Returns a clean, minimal QR page for receiving tips.

    Displays a scannable QR code with the specified amount.
    The amount is fixed and cannot be edited by the user.

    **Parameters:**
    - `lightning_address`: Lightning address to receive tips
    - `tip_amount`: Amount in satoshis

    **Example:** `/tip/bitkarrot@nostr.com/amt/100`
    """

    try:
        # Get QR page data with the specified amount
        data = await get_qr_page_data(lightning_address, int(tip_amount))

        return templates.TemplateResponse('qr_clean.html',
                context={'request': request,
                        'lnaddress': lightning_address,
                        'bolt11': data['bolt11'],
                        'qrdata': data['qr'],
                        'qr_png': data.get('qr_png', ''),
                        'amount': tip_amount})
    except Exception as e:
        return [{
            "msg" : "Not a valid tipping Address. Sorry!",
            "error": "Error {0}".format(str(e))
        }]


@app.get('/qr/{lightning_address}')
async def get_QR_Code_From_LN_Address(lightning_address: str):
    """
    Returns a QR code PNG image for the Lightning Address.

    The QR code contains a BOLT11 invoice (no amount specified, uses min).

    **Example:** `/qr/bitkarrot@nostr.com`
    """
    try:
        if lightning_address is not None:
            tip_file = '/tmp/qr_lnaddy.png'
            bolt11 = await get_bolt(lightning_address, None)
            #print(bolt11)
            qr = pyqrcode.create(bolt11)
            qr.png(tip_file, scale=3, module_color=[0,0,0,128], background=[0xff, 0xff, 0xff])
            return FileResponse(tip_file)
        else:
            return [{
                "msg" : "Please send a valid Lightning Address"
            }]
    except Exception as e:
        return [{
            "msg" : "QR code from LN: Not a valid Lightning Address. Sorry!",
            "error": "Error {0}".format(str(e))
        }]


async def get_svg_from_qr(qr,  st: str = None, bg: str = None):
    try:
        stream = BytesIO()
        bgcolor = "white"
        modcolor = "black"
        if (st is not None):
            modcolor = st
        if (bg is not None):
            bgcolor = bg

        qr.svg(stream, scale=3, background=bgcolor, module_color=modcolor)

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
        return [{
            "msg" : "Not a valid Lightning Address"
        }]


async def get_png_base64_from_qr(qr):
    """Generate QR code as base64-encoded PNG for HTML embedding"""
    import base64
    try:
        stream = BytesIO()
        # Use same parameters as the working /qr endpoint
        qr.png(stream, scale=3, module_color=[0, 0, 0, 128], background=[0xff, 0xff, 0xff])
        png_data = stream.getvalue()
        base64_data = base64.b64encode(png_data).decode('utf-8')
        return f"data:image/png;base64,{base64_data}"
    except Exception as e:
        logging.error(e)
        return None


@app.post("/{lightning_address}")
async def post_to_QR_Endpoint(lightning_address, request: Request, amount: int = Form(...)):
    """
    this endpoint is a POST request
    that will get the QR code for sending sats from the lightning address
    amount used is submitted by the user via the in page form.
    example use: /user@domain.com
    """

    try:
        #print("Amount posted : " + str(amount))
        if type(amount) is not int:
            raise Exception("amount must be an integer")

        if '@' in lightning_address:
            #print("inside get /lightningaddress, default amount no value, use None")
            data = await get_qr_page_data(lightning_address, amount)

            return templates.TemplateResponse('sats.html',
                                    context={'request': request,
                                            'lnaddress': lightning_address,
                                            'bolt11': data['bolt11'],
                                            'url': data['url'],
                                            'min_send': data['min'],
                                            'max_send': data['max'],
                                            'callback': data['callback_data'],
                                            'amount': data['amount'],
                                            'pr_dict': data['pr_dict'],
                                            'qrdata': data['qr']})
        else:
            return [{
                "msg" : "Please send a valid Lightning Address",
            }]

    except Exception as e:
        logging.error(e)
        print(e)
        return [{
            "msg" : "Not a valid Lightning Address",
            "error": "Error {0}".format(str(e))
        }]





@app.get("/{lightning_address}")
async def forward_to_QR_Endpoint(
    lightning_address: str,
    request: Request,
    amount: int = Query(None),
    memo: str = Query(None)
):
    """
    Get QR code page for a Lightning Address.

    - **With query params** (clean QR page): Returns a minimal, scannable QR page
    - **Without query params**: Returns full page with form to enter custom amount

    **Parameters:**
    - `lightning_address`: Lightning address (e.g., user@domain.com)
    - `amount`: Optional amount in satoshis (integer)
    - `memo`: Optional memo/note for the payment (string)

    **Examples:**
    - `/{ln}` - Full page with form
    - `/{ln}?amount=10000` - Clean QR page for 10000 sats
    - `/{ln}?amount=100&memo=forservices` - Clean QR page with memo
    """
    try:
        if '@' in lightning_address:
            # Use provided amount from query param, or None to use min amount
            data = await get_qr_page_data(lightning_address, amount)

            # Use clean template if amount or memo is provided via query params
            use_clean_template = amount is not None or memo is not None

            template_name = 'qr_clean.html' if use_clean_template else 'sats.html'
            display_amount = amount if amount else data['min']

            context = {
                'request': request,
                'lnaddress': lightning_address,
                'bolt11': data['bolt11'],
                'qrdata': data['qr'],
                'qr_png': data.get('qr_png', ''),
                'amount': display_amount,
            }

            # Add memo to context if provided
            if memo:
                context['memo'] = memo

            # For the detailed template, add more context
            if not use_clean_template:
                context.update({
                    'url': data['url'],
                    'min_send': data['min'],
                    'max_send': data['max'],
                    'callback': data['callback_data'],
                    'pr_dict': data['pr_dict'],
                })

            return templates.TemplateResponse(template_name, context=context)
        else:
            return [{
                "msg" : "Please send a valid Lightning Address",
            }]

    except Exception as e:
        logging.error(e)
        print(e)
        return [{
            "msg" : "Not a valid Lightning Address",
            "error": "Error {0}".format(str(e))
        }]



@app.get('/bolt11/{lightning_address}/amt/{amount}')
async def get_qr_via_bolt11(lightning_address: str, amount: str):
    """
    Returns a BOLT11 invoice as JSON.

    **Parameters:**
    - `lightning_address`: Lightning address
    - `amount`: Amount in satoshis

    **Response:** `{"bolt11": "LNBC..."}`

    **Example:** `/bolt11/bitkarrot@nostr.com/amt/100`
    """
    try:
        if lightning_address is not None:
            bolt11 = await get_bolt(lightning_address, int(amount))
            # TODO >>>>> check if bolt11 is valid
            return {
                "bolt11" : bolt11
            }
        else:
            return [{
                "msg" : "Please send give a lightning address"
            }]
    except Exception as e:
        print(e)
        return [{
            "msg" : "Not a valid Lightning Address"
        }]


@app.get("/svg/{lightning_address}/amt/{amount}")
async def get_svg_LN_address_amt(lightning_address: str, amount: str, st: str = None, bg: str = None):
    """
    Returns a QR code in SVG format.

    **Parameters:**
    - `lightning_address`: Lightning address
    - `amount`: Amount in satoshis
    - `st`: Optional stroke/module color (default: black)
    - `bg`: Optional background color (default: white)

    **Example:** `/svg/bitkarrot@nostr.com/amt/100`
    """
    try:
        # logging.info("LN Address", lightning_address, "tip amount: ", amount)
        # logging.info("bgcolor: ", bg, "stroke: ", st)
        #print("LN Address", lightning_address, "tip amount: ", amount)
        #print("bgcolor: ", bg, "stroke: ", st)

        bolt11 = await get_bolt(lightning_address, int(amount))
        qr = pyqrcode.create(bolt11)

        stream = BytesIO()
        bgcolor = "white"
        modcolor = "black"
        if (st is not None):
            modcolor = st
        if (bg is not None):
            bgcolor = bg

        qr.svg(stream, scale=3, background=bgcolor, module_color=modcolor)

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
        return [{
            "msg" : "Not a valid Lightning Address"
        }]


# for local testing
if __name__ == "__main__":
  uvicorn.run("app:app", host="localhost", port=5000, reload=True)
