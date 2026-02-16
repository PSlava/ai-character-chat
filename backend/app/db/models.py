import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, Integer, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
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


class RelationType(str, enum.Enum):
    rival = "rival"
    ex = "ex"
    friend = "friend"
    sibling = "sibling"
    enemy = "enemy"
    lover = "lover"
    ally = "ally"


def gen_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    oauth_provider: Mapped[str | None] = mapped_column(String, nullable=True)
    oauth_id: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String, nullable=True, default="ru")
    role: Mapped[str] = mapped_column(String, default="user")  # "admin" | "user"
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    chat_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    characters: Mapped[list["Character"]] = relationship(back_populates="creator")
    chats: Mapped[list["Chat"]] = relationship(back_populates="user")
    personas: Mapped[list["Persona"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    creator_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    slug: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    tagline: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    personality: Mapped[str] = mapped_column(Text, nullable=False)
    scenario: Mapped[str | None] = mapped_column(Text, nullable=True)
    greeting_message: Mapped[str] = mapped_column(Text, nullable=False)
    example_dialogues: Mapped[str | None] = mapped_column(Text, nullable=True)
    appearance: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_rating: Mapped[ContentRating] = mapped_column(
        SAEnum(ContentRating), default=ContentRating.sfw
    )
    system_prompt_suffix: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str] = mapped_column(String, default="")  # comma-separated
    structured_tags: Mapped[str] = mapped_column(String, default="")  # comma-separated tag IDs
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    chat_count: Mapped[int] = mapped_column(Integer, default=0)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    base_chat_count: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)  # {"ru": 345, "en": 567}
    base_like_count: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)  # {"ru": 75, "en": 62}
    preferred_model: Mapped[str] = mapped_column(String, default="claude")
    max_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True, default=2048)
    response_length: Mapped[str | None] = mapped_column(String, nullable=True, default="long")
    message_counts: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)  # {"ru": 150, "en": 30}
    original_language: Mapped[str] = mapped_column(String, default="ru")
    translations: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)  # {"en": {"name": "...", "tagline": "...", "tags": [...]}}
    vote_score: Mapped[int] = mapped_column(Integer, default=0)
    fork_count: Mapped[int] = mapped_column(Integer, default=0)
    forked_from_id: Mapped[str | None] = mapped_column(ForeignKey("characters.id", ondelete="SET NULL"), nullable=True)
    highlights: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)  # [{"text": "...", "lang": "ru"}, ...]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator: Mapped["User"] = relationship(back_populates="characters")
    chats: Mapped[list["Chat"]] = relationship(back_populates="character", cascade="all, delete-orphan")
    forked_from: Mapped["Character | None"] = relationship(remote_side="Character.id", foreign_keys=[forked_from_id])


class Persona(Base):
    __tablename__ = "personas"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="personas")
    chats: Mapped[list["Chat"]] = relationship(back_populates="persona")


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    character_id: Mapped[str] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    persona_id: Mapped[str | None] = mapped_column(ForeignKey("personas.id", ondelete="SET NULL"), nullable=True)
    persona_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    persona_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # LLM-generated summary of older messages
    summary_up_to_id: Mapped[str | None] = mapped_column(String, nullable=True)  # last message ID included in summary
    anon_session_id: Mapped[str | None] = mapped_column(String, nullable=True)  # anonymous guest session
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="chats")
    character: Mapped["Character"] = relationship(back_populates="chats")
    persona: Mapped["Persona | None"] = relationship(back_populates="chats")
    messages: Mapped[list["Message"]] = relationship(back_populates="chat", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    chat_id: Mapped[str] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    role: Mapped[MessageRole] = mapped_column(SAEnum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    chat: Mapped["Chat"] = relationship(back_populates="messages")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    reporter_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    character_id: Mapped[str] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    reason: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Favorite(Base):
    __tablename__ = "favorites"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    character_id: Mapped[str] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    key: Mapped[str] = mapped_column(String, primary_key=True)  # "ru.intro", "en.length_long"
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Vote(Base):
    __tablename__ = "votes"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    character_id: Mapped[str] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), primary_key=True)
    value: Mapped[int] = mapped_column(Integer, nullable=False)  # +1 or -1
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CharacterRelation(Base):
    __tablename__ = "character_relations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    character_id: Mapped[str] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    related_id: Mapped[str] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    relation_type: Mapped[str] = mapped_column(String(20), nullable=False)  # RelationType value
    label_ru: Mapped[str | None] = mapped_column(String, nullable=True)
    label_en: Mapped[str | None] = mapped_column(String, nullable=True)
    label_es: Mapped[str | None] = mapped_column(String, nullable=True)
    label_fr: Mapped[str | None] = mapped_column(String, nullable=True)
    label_de: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GroupChat(Base):
    __tablename__ = "group_chats"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    members: Mapped[list["GroupChatMember"]] = relationship(back_populates="group_chat", cascade="all, delete-orphan")
    messages: Mapped[list["GroupMessage"]] = relationship(back_populates="group_chat", cascade="all, delete-orphan")


class GroupChatMember(Base):
    __tablename__ = "group_chat_members"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    group_chat_id: Mapped[str] = mapped_column(ForeignKey("group_chats.id", ondelete="CASCADE"))
    character_id: Mapped[str] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer, default=0)

    group_chat: Mapped["GroupChat"] = relationship(back_populates="members")
    character: Mapped["Character"] = relationship()


class GroupMessage(Base):
    __tablename__ = "group_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    group_chat_id: Mapped[str] = mapped_column(ForeignKey("group_chats.id", ondelete="CASCADE"))
    character_id: Mapped[str | None] = mapped_column(ForeignKey("characters.id", ondelete="SET NULL"), nullable=True)  # null for user messages
    role: Mapped[MessageRole] = mapped_column(SAEnum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    model_used: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    group_chat: Mapped["GroupChat"] = relationship(back_populates="messages")


class LoreEntry(Base):
    __tablename__ = "lore_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    character_id: Mapped[str] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    keywords: Mapped[str] = mapped_column(String, nullable=False)  # comma-separated trigger words
    content: Mapped[str] = mapped_column(Text, nullable=False)  # lore text to inject
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    position: Mapped[int] = mapped_column(Integer, default=0)  # sort order
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PageView(Base):
    __tablename__ = "page_views"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    path: Mapped[str] = mapped_column(String, nullable=False)
    ip_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String, nullable=True)
    device: Mapped[str | None] = mapped_column(String(10), nullable=True)  # mobile/desktop/tablet
    referrer: Mapped[str | None] = mapped_column(String, nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
