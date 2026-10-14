"""Foydali buyruqlar: purge, del, echo."""
from ._helpers import command, register_all


@command("del", "Javob berilgan xabarni o'chiradi")
async def delete_msg(event):
    reply = await event.get_reply_message()
    if reply:
        await reply.delete()
    await event.delete()


@command("purge", "Javob berilgan xabardan boshlab hammasini o'chiradi")
async def purge(event):
    reply = await event.get_reply_message()
    if not reply:
        await event.edit("Nimadan boshlab o'chirishni ko'rsatish uchun xabarga javob bering.")
        return
    msgs = []
    async for msg in event.client.iter_messages(
        event.chat_id, min_id=reply.id - 1, reverse=True
    ):
        msgs.append(msg)
        if len(msgs) == 100:
            await event.client.delete_messages(event.chat_id, msgs)
            msgs = []
    if msgs:
        await event.client.delete_messages(event.chat_id, msgs)


@command("echo", "Yozilgan matnni qaytaradi (.echo salom)")
async def echo(event):
    text = event.pattern_match.group(1)
    if text:
        await event.edit(text)


def register(client):
    register_all(client, __import__(__name__, fromlist=["_"]))
