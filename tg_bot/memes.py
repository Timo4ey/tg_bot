import asyncio
import functools
import json
import re

import aiohttp
from telegram import Chat, InputMediaPhoto
from telegram.ext import ContextTypes


async def send_memes(
    url: str, chat_id: int, text: str, context: ContextTypes
) -> None:
    """ "Send posts memes to a chat"""
    bot = context.bot

    try:
        await bot.send_photo(photo=url, chat_id=chat_id, caption=text)
    except Exception as _ex:
        print(_ex)


async def send_carousels(
    urls: list, chat_id: int, text: str, context: ContextTypes
) -> None:
    """ "Send send_carousels memes to a chat"""
    bot = context.bot

    try:
        await bot.send_media_group(media=urls, chat_id=chat_id, caption=text)
    except Exception as _ex:
        print(_ex)


def get_data():
    """Decorator for getting post and carousels"""

    def inner(func):
        @functools.wraps(func)
        async def wrapped(link, *args, **kwargs):
            async with aiohttp.ClientSession(trust_env=True) as session:
                async with session.get(link, ssl=False) as response:
                    data = await response.text()
                    data = json.loads(data)
                    result = await func(data, *args, **kwargs)
                return result

        return wrapped

    return inner


@get_data()
async def get_data_for_posts(data, chat_id, context):
    for x in data:
        url = x.get("url")
        text = x.get("text")
        await send_memes(url=url, text=text, chat_id=chat_id, context=context)


@get_data()
async def get_data_for_carousels(data, chat_id, context):
    for _dict in data:
        del _dict["carousel_id"]
        del _dict["content_fk"]
        media = []
        text = ""
        for k, v in _dict.items():
            if v and k.find("url") != -1:
                media.append(InputMediaPhoto(media=v))
            else:
                text = v
        await asyncio.sleep(0.5)
        await send_carousels(
            urls=media, text=text, chat_id=chat_id, context=context
        )


async def get_posts(chat_id, context, hours):
    task1 = asyncio.create_task(
        get_data_for_posts(
            f"http://172.17.0.1:8000/api/v1/posts/?hours={hours}",
            chat_id,
            context,
        )
    )
    await asyncio.gather(task1)


async def get_carousels(chat_id, context, hours):
    task1 = asyncio.create_task(
        get_data_for_carousels(
            f"http://172.17.0.1:8000/api/v1/carousel/?hours={hours}",
            chat_id,
            context,
        )
    )
    await asyncio.gather(task1)


def post_data(link):
    """Decorator for posting post and carousels"""

    def inner(func):
        @functools.wraps(func)
        async def wrapped(user_data: Chat, *args, **kwargs):
            async with aiohttp.ClientSession(trust_env=True) as session:
                func_res = await func(user_data, *args, **kwargs)
                result = await session.post(url=link, data=func_res)
                return result

        return wrapped

    return inner


async def get_group_name(data: str) -> str:
    return re.findall(r"(?<=group ).*(?= id)", data)[0]


async def get_group_id(data: str) -> str:
    return re.findall(r"(?<= id ).\d+", data)[0]


@post_data("http://172.17.0.1:8000/api/v1/telegram_users/")
async def save_user(user_data: Chat) -> dict:
    return {
        "telegram_id": user_data.id,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "username": user_data.username,
    }


async def is_valid_group(data: list) -> None:
    """it will check if id is valid and group is unique"""
    return True


@post_data("http://172.17.0.1:8000/api/v1/groups/")
async def save_group(user_data: dict) -> dict:
    group_name = await get_group_name(user_data)
    group_id = await get_group_id(user_data)
    return {
        "group_name": group_name,
        "group_vk_id": group_id,
    }


if __name__ == "__main__":
    asyncio.run(get_posts())
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(get_text_and_link('http://127.0.0.1:8000/api/v1/posts/?hours=66'))
