import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/hooks/useAuth';
import { useAuthStore } from '@/store/authStore';
import { signOut } from '@/api/auth';
import { Button } from '@/components/ui/Button';
import { LanguageSwitcher } from '@/components/ui/LanguageSwitcher';
import { Logo } from '@/components/ui/Logo';
import { Plus, LogOut, User, Menu } from 'lucide-react';

interface Props {
  onToggleSidebar?: () => void;
}

export function Header({ onToggleSidebar }: Props) {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuth();
  const { logout } = useAuthStore();

  const handleLogout = () => {
    signOut();
    logout();
  };

  return (
    <header className="h-14 border-b border-neutral-800 flex items-center justify-between px-3 sm:px-4 bg-neutral-900/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="flex items-center gap-2">
        {onToggleSidebar && (
          <button
            onClick={onToggleSidebar}
            className="p-1.5 text-neutral-400 hover:text-white transition-colors md:hidden"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}
        <Link to="/" className="flex items-center gap-1.5 text-lg font-bold">
          <Logo className="w-6 h-6 text-purple-500" />
          <span className="hidden sm:inline">
            <span className="text-white">Interactive</span><span className="text-purple-500">Fiction</span>
          </span>
        </Link>
      </div>

      <div className="flex items-center gap-1 sm:gap-2">
        <LanguageSwitcher compact />
        {isAuthenticated ? (
          <>
            <Link to="/create">
              <Button variant="secondary" size="sm" className="flex items-center gap-1">
                <Plus className="w-4 h-4" />
                <span className="hidden sm:inline">{t('header.create')}</span>
              </Button>
            </Link>
            <Link to="/profile">
              <Button variant="ghost" size="sm">
                <User className="w-4 h-4" />
              </Button>
            </Link>
            <Button variant="ghost" size="sm" onClick={handleLogout}>
              <LogOut className="w-4 h-4" />
            </Button>
          </>
        ) : (
          <Link to="/auth">
            <Button size="sm">{t('header.login')}</Button>
          </Link>
        )}
      </div>
    </header>
  );
}
