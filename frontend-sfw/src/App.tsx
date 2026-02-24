import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { LangRoute } from '@/components/routing/LangRoute';
import { LangRedirect } from '@/components/routing/LangRedirect';

// Regular imports — needed on first load or lightweight static pages
import { HomePage } from '@/pages/HomePage';
import { AuthPage } from '@/pages/AuthPage';
import { CharacterPage } from '@/pages/CharacterPage';
import { AboutPage } from '@/pages/AboutPage';
import { TermsPage } from '@/pages/TermsPage';
import { PrivacyPage } from '@/pages/PrivacyPage';
import { FAQPage } from '@/pages/FAQPage';
import { TagLandingPage } from '@/pages/TagLandingPage';

// Lazy imports — heavy pages not needed on first load
const ChatPage = lazy(() => import('@/pages/ChatPage').then(m => ({ default: m.ChatPage })));
const CreateCharacterPage = lazy(() => import('@/pages/CreateCharacterPage').then(m => ({ default: m.CreateCharacterPage })));
const EditCharacterPage = lazy(() => import('@/pages/EditCharacterPage').then(m => ({ default: m.EditCharacterPage })));
const ProfilePage = lazy(() => import('@/pages/ProfilePage').then(m => ({ default: m.ProfilePage })));
const FavoritesPage = lazy(() => import('@/pages/FavoritesPage').then(m => ({ default: m.FavoritesPage })));
const AdminPromptsPage = lazy(() => import('@/pages/AdminPromptsPage').then(m => ({ default: m.AdminPromptsPage })));
const AdminUsersPage = lazy(() => import('@/pages/AdminUsersPage').then(m => ({ default: m.AdminUsersPage })));
const AdminAnalyticsPage = lazy(() => import('@/pages/AdminAnalyticsPage').then(m => ({ default: m.AdminAnalyticsPage })));
const OAuthCallbackPage = lazy(() => import('@/pages/OAuthCallbackPage').then(m => ({ default: m.OAuthCallbackPage })));
const ResetPasswordPage = lazy(() => import('@/pages/ResetPasswordPage').then(m => ({ default: m.ResetPasswordPage })));

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={null}>
        <Routes>
          <Route element={<Layout />}>
            {/* SEO pages — language-prefixed */}
            <Route path="/:lang" element={<LangRoute />}>
              <Route index element={<HomePage />} />
              <Route path="c/:slug" element={<CharacterPage />} />
              <Route path="character/:id" element={<CharacterPage />} />
              <Route path="about" element={<AboutPage />} />
              <Route path="terms" element={<TermsPage />} />
              <Route path="privacy" element={<PrivacyPage />} />
              <Route path="faq" element={<FAQPage />} />
              <Route path="tags/:tagName" element={<TagLandingPage />} />
            </Route>

            {/* Legacy bare paths → redirect to /:lang/... */}
            <Route path="/" element={<LangRedirect />} />
            <Route path="/c/:slug" element={<LangRedirect />} />
            <Route path="/about" element={<LangRedirect />} />
            <Route path="/terms" element={<LangRedirect />} />
            <Route path="/privacy" element={<LangRedirect />} />
            <Route path="/faq" element={<LangRedirect />} />
            <Route path="/tags/:tagName" element={<LangRedirect />} />

            {/* Non-SEO pages — no language prefix */}
            <Route path="/auth" element={<AuthPage />} />
            <Route path="/auth/reset-password" element={<ResetPasswordPage />} />
            <Route path="/auth/oauth-callback" element={<OAuthCallbackPage />} />
            <Route path="/character/:id/edit" element={<EditCharacterPage />} />
            <Route path="/chat/:chatId" element={<ChatPage />} />
            <Route path="/create" element={<CreateCharacterPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/favorites" element={<FavoritesPage />} />
            <Route path="/admin/prompts" element={<AdminPromptsPage />} />
            <Route path="/admin/users" element={<AdminUsersPage />} />
            <Route path="/admin/analytics" element={<AdminAnalyticsPage />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
