import os

from telethon.sessions import StringSession
from telethon.tl.types import User, Chat, PeerUser, Channel

from core.entities import Message, TelegramUser, TelegramDialog, TelegramChat, \
    TelegramChannel
from core.message_provider import IMessageProvider
# from telethon import TelegramClient
from telethon.sync import TelegramClient

from config import (API_ID, API_HASH)


class TelegramMessageProvider(IMessageProvider):
    async def authorize_user(self, phone_number: str, password: str = None,
                             code: str = None) -> TelegramUser:
        client = TelegramClient('user-session', API_ID, API_HASH)

        session_key = StringSession.save(client.session)
        os.environ['SESSION_KEY'] = session_key
        with open('session.txt', 'w') as txt_file:
            txt_file.write(session_key)

        await client.start(
            phone=lambda: phone_number,
            password=lambda: password,
            code_callback=lambda: code,
            max_attempts=1,
        )

        user = await client.get_me()

        return TelegramUser(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            phone=user.phone,
        )

    async def get_user_dialogs(self) -> list[TelegramDialog]:
        session_key = os.environ.get('SESSION_KEY')
        if not session_key:
            with open('session.txt', 'r') as txt_file:
                session_key = txt_file.read()

        client = TelegramClient(StringSession(session_key), API_ID, API_HASH)
        await client.connect()

        dialogs = await client.get_dialogs()

        result = []
        for dialog in dialogs:
            if isinstance(dialog.entity, User):
                entity = TelegramUser(
                    id=dialog.entity.id,
                    first_name=dialog.entity.first_name,
                    last_name=dialog.entity.last_name,
                    username=dialog.entity.username,
                    phone=dialog.entity.phone
                )
            elif isinstance(dialog.entity, Channel):
                entity = TelegramChannel(
                    id=dialog.entity.id,
                    title=dialog.entity.title,
                    creator=dialog.entity.creator,
                    username=dialog.entity.username,
                )
            else:
                entity = TelegramChat(
                    id=dialog.entity.id,
                    title=dialog.entity.title,
                    creator=dialog.entity.creator,
                )

            try:
                if isinstance(dialog.message.from_id, PeerUser):
                    sender_id = dialog.message.from_id.user_id
                else:
                    sender_id = dialog.message.from_id.channel_id
            except AttributeError:
                if isinstance(dialog.message.peer_id, PeerUser):
                    sender_id = dialog.message.peer_id.user_id
                else:
                    sender_id = dialog.message.peer_id.channel_id

            message = Message(
                sender_id=sender_id,
                text=dialog.message.message,
                created_at=dialog.message.date
            )

            result.append(TelegramDialog(
                name=dialog.name,
                entity=entity,
                message=message
            ))

        return result

    async def get_dialog_messages(self, dialog_type: str, dialog_id: str) -> \
            list[Message]:
        session_key = os.environ.get('SESSION_KEY')
        if not session_key:
            with open('session.txt', 'r') as txt_file:
                session_key = txt_file.read()

        client = TelegramClient(StringSession(session_key), API_ID, API_HASH)
        await client.connect()

        if dialog_type == 'chat':
            entity = await client.get_input_entity(-int(dialog_id))
        elif dialog_type == 'channel':
            channel_id = str(-100) + dialog_id
            entity = await client.get_input_entity(int(channel_id))
        else:
            entity = await client.get_input_entity(int(dialog_id))

        messages = await client.get_messages(
            entity=entity,
            limit=30
        )

        result = []
        for message in messages:
            try:
                if isinstance(message.from_id, PeerUser):
                    sender_id = message.from_id.user_id
                else:
                    sender_id = message.from_id.channel_id
            except AttributeError:
                if isinstance(message.peer_id, PeerUser):
                    sender_id = message.peer_id.user_id
                else:
                    sender_id = message.peer_id.channel_id

            message = Message(
                sender_id=sender_id,
                text=message.message,
                created_at=message.date
            )

            result.append(message)

        return result

    def send_message(self, message: Message):
        pass
