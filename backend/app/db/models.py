import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, Integer, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    pass


class ContentRating(str, enum.Enum):
    sfw = "sfw"
    moderate = "moderate"
    nsfw = "nsfw"


class MessageRole(str, enum.Enum):
    system = "system"
    user = "user"
    assistant = "assistant"


def gen_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String, nullable=True, default="ru")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    characters: Mapped[list["Character"]] = relationship(back_populates="creator")
    chats: Mapped[list["Chat"]] = relationship(back_populates="user")


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    creator_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    tagline: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    personality: Mapped[str] = mapped_column(Text, nullable=False)
    scenario: Mapped[str | None] = mapped_column(Text, nullable=True)
    greeting_message: Mapped[str] = mapped_column(Text, nullable=False)
    example_dialogues: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_rating: Mapped[ContentRating] = mapped_column(
        SAEnum(ContentRating), default=ContentRating.sfw
    )
    system_prompt_suffix: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str] = mapped_column(String, default="")  # comma-separated
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    chat_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    preferred_model: Mapped[str] = mapped_column(String, default="claude")
    max_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True, default=2048)
    response_length: Mapped[str | None] = mapped_column(String, nullable=True, default="long")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator: Mapped["User"] = relationship(back_populates="characters")
    chats: Mapped[list["Chat"]] = relationship(back_populates="character", cascade="all, delete-orphan")


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    character_id: Mapped[str] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="chats")
    character: Mapped["Character"] = relationship(back_populates="chats")
    messages: Mapped[list["Message"]] = relationship(back_populates="chat", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    chat_id: Mapped[str] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    role: Mapped[MessageRole] = mapped_column(SAEnum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    chat: Mapped["Chat"] = relationship(back_populates="messages")


class Favorite(Base):
    __tablename__ = "favorites"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    character_id: Mapped[str] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
