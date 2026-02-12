import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { HomePage } from '@/pages/HomePage';
import { AuthPage } from '@/pages/AuthPage';
import { CharacterPage } from '@/pages/CharacterPage';
import { ChatPage } from '@/pages/ChatPage';
import { CreateCharacterPage } from '@/pages/CreateCharacterPage';
import { EditCharacterPage } from '@/pages/EditCharacterPage';
import { ProfilePage } from '@/pages/ProfilePage';
import { FavoritesPage } from '@/pages/FavoritesPage';
import { AdminPromptsPage } from '@/pages/AdminPromptsPage';
import { ResetPasswordPage } from '@/pages/ResetPasswordPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/auth/reset-password" element={<ResetPasswordPage />} />
          <Route path="/character/:id" element={<CharacterPage />} />
          <Route path="/character/:id/edit" element={<EditCharacterPage />} />
          <Route path="/chat/:chatId" element={<ChatPage />} />
          <Route path="/create" element={<CreateCharacterPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/favorites" element={<FavoritesPage />} />
          <Route path="/admin/prompts" element={<AdminPromptsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
