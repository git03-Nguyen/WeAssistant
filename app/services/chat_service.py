from sqlalchemy.ext.asyncio import AsyncSession


class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session
