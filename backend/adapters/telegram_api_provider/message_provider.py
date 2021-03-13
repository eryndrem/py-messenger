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
    # current_user = None
    current_user = TelegramUser(
        id=412300498,
        first_name='Eryn',
        last_name='Drem',
        username='eryndrem',
        phone='79530490707',
    )

    @staticmethod
    def get_authorized_user_session():
        session_key = os.environ.get('SESSION_KEY')
        if not session_key:
            with open('session.txt', 'r') as txt_file:
                session_key = txt_file.read()

        return TelegramClient(StringSession(session_key), API_ID, API_HASH)

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

        self.current_user = TelegramUser(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            phone=user.phone,
        )

        return self.current_user

    async def get_user_dialogs(self) -> list[TelegramDialog]:
        client = self.get_authorized_user_session()
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
                id=dialog.message.id,
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

    async def get_dialog_messages(self, dialog_id: str, offset: str,
                                  limit: str) -> list[Message]:
        client = self.get_authorized_user_session()
        await client.connect()

        entity = await client.get_input_entity(int(dialog_id))

        messages = await client.get_messages(
            entity=entity,
            limit=int(limit),
            add_offset=int(offset)
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
                id=message.id,
                sender_id=sender_id,
                text=message.message,
                created_at=message.date
            )

            result.append(message)

        return result

    async def send_message(self, receiver_id: str, message: str) -> Message:
        client = self.get_authorized_user_session()
        await client.connect()

        entity = await client.get_input_entity(int(receiver_id))

        message = await client.send_message(
            entity=entity,
            message=message
        )

        return Message(
            id=message.id,
            sender_id=self.current_user.id,
            text=message.message,
            created_at=message.date
        )
