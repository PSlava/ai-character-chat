-- ============================================
-- PROFILES (extends auth.users)
-- ============================================
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT,
    avatar_url TEXT,
    bio TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, username, display_name)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'username', 'user_' || substr(NEW.id::text, 1, 8)),
        COALESCE(NEW.raw_user_meta_data->>'display_name', 'Пользователь')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================
-- CHARACTERS
-- ============================================
CREATE TYPE content_rating AS ENUM ('sfw', 'moderate', 'nsfw');

CREATE TABLE public.characters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    tagline TEXT,
    avatar_url TEXT,
    personality TEXT NOT NULL,
    scenario TEXT,
    greeting_message TEXT NOT NULL,
    example_dialogues TEXT,
    content_rating content_rating DEFAULT 'sfw',
    system_prompt_suffix TEXT,
    tags TEXT[] DEFAULT '{}',
    is_public BOOLEAN DEFAULT true,
    chat_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    preferred_model TEXT DEFAULT 'claude',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_characters_creator ON public.characters(creator_id);
CREATE INDEX idx_characters_public ON public.characters(is_public, created_at DESC);
CREATE INDEX idx_characters_tags ON public.characters USING gin(tags);

-- ============================================
-- CHATS
-- ============================================
CREATE TABLE public.chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    character_id UUID NOT NULL REFERENCES public.characters(id) ON DELETE CASCADE,
    title TEXT,
    model_used TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_chats_user ON public.chats(user_id, updated_at DESC);
CREATE INDEX idx_chats_character ON public.chats(character_id);

-- ============================================
-- MESSAGES
-- ============================================
CREATE TYPE message_role AS ENUM ('system', 'user', 'assistant');

CREATE TABLE public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID NOT NULL REFERENCES public.chats(id) ON DELETE CASCADE,
    role message_role NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_messages_chat ON public.messages(chat_id, created_at ASC);

-- ============================================
-- FAVORITES
-- ============================================
CREATE TABLE public.favorites (
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    character_id UUID REFERENCES public.characters(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (user_id, character_id)
);

-- ============================================
-- ROW LEVEL SECURITY
-- ============================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.characters ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.favorites ENABLE ROW LEVEL SECURITY;

-- Profiles
CREATE POLICY "Profiles are viewable by everyone"
    ON public.profiles FOR SELECT USING (true);
CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- Characters
CREATE POLICY "Public characters are viewable"
    ON public.characters FOR SELECT
    USING (is_public = true OR creator_id = auth.uid());
CREATE POLICY "Users can create characters"
    ON public.characters FOR INSERT
    WITH CHECK (creator_id = auth.uid());
CREATE POLICY "Creators can update own characters"
    ON public.characters FOR UPDATE USING (creator_id = auth.uid());
CREATE POLICY "Creators can delete own characters"
    ON public.characters FOR DELETE USING (creator_id = auth.uid());

-- Chats
CREATE POLICY "Users see own chats"
    ON public.chats FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Users can create chats"
    ON public.chats FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY "Users can delete own chats"
    ON public.chats FOR DELETE USING (user_id = auth.uid());

-- Messages
CREATE POLICY "Users see messages of own chats"
    ON public.messages FOR SELECT
    USING (EXISTS (SELECT 1 FROM public.chats WHERE chats.id = messages.chat_id AND chats.user_id = auth.uid()));
CREATE POLICY "Users can insert messages into own chats"
    ON public.messages FOR INSERT
    WITH CHECK (EXISTS (SELECT 1 FROM public.chats WHERE chats.id = messages.chat_id AND chats.user_id = auth.uid()));

-- Favorites
CREATE POLICY "Users see own favorites"
    ON public.favorites FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "Users can favorite"
    ON public.favorites FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY "Users can unfavorite"
    ON public.favorites FOR DELETE USING (user_id = auth.uid());
