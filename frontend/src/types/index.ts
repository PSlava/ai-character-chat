export interface Profile {
  id: string;
  username: string;
  display_name: string | null;
  avatar_url: string | null;
  bio: string | null;
}

export interface Character {
  id: string;
  creator_id: string;
  name: string;
  tagline: string | null;
  avatar_url: string | null;
  personality: string;
  scenario: string | null;
  greeting_message: string;
  example_dialogues: string | null;
  content_rating: 'sfw' | 'moderate' | 'nsfw';
  system_prompt_suffix: string | null;
  tags: string[];
  is_public: boolean;
  chat_count: number;
  like_count: number;
  preferred_model: string;
  max_tokens: number;
  response_length: 'short' | 'medium' | 'long' | 'very_long';
  created_at: string;
  profiles?: Pick<Profile, 'username' | 'display_name' | 'avatar_url'>;
}

export interface Chat {
  id: string;
  user_id: string;
  character_id: string;
  title: string | null;
  model_used: string | null;
  created_at: string;
  updated_at: string;
  characters?: Character;
}

export interface Message {
  id: string;
  chat_id: string;
  role: 'system' | 'user' | 'assistant';
  content: string;
  created_at: string;
  isError?: boolean;
}

export interface ChatDetail {
  chat: Chat;
  messages: Message[];
}
