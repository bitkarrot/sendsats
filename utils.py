import json

"""
 utils for aiohttp. 
"""

async def get_url(session, path, headers) -> str:
    """
    aiohttp: for use with GET requests
    """
    async with session.get(path, headers=headers) as resp:
        res = await resp.read()
        return res


async def post_jurl(session, path, headers, json) -> json:
    """
    aiohttp: for use with JSON in POST requests
    """
    async with session.post(url=path, headers=headers, json=json) as resp:
        res = await resp.json()
        return res


async def post_url(session, path, headers, body) -> json:
    """
    aiohttp: for use with BODY in POST requests
    """
    async with session.post(url=path, headers=headers, data=body) as resp:
        res = await resp.json()
        return res


async def delete_url(session, path, headers) -> str:
    """
    aiohttp: for use with DELETE requests
    """
    async with session.delete(path, headers=headers) as resp:
        res = await resp.text()
        return res
