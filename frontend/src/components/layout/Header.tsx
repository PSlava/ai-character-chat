import { Link } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useAuthStore } from '@/store/authStore';
import { signOut } from '@/api/auth';
import { Button } from '@/components/ui/Button';
import { MessageCircle, Plus, LogOut, User } from 'lucide-react';

export function Header() {
  const { isAuthenticated } = useAuth();
  const { logout } = useAuthStore();

  const handleLogout = () => {
    signOut();
    logout();
  };

  return (
    <header className="h-14 border-b border-neutral-800 flex items-center justify-between px-4 bg-neutral-900/80 backdrop-blur-sm sticky top-0 z-50">
      <Link to="/" className="flex items-center gap-2 text-lg font-bold">
        <MessageCircle className="w-6 h-6 text-purple-500" />
        <span>AI Chat</span>
      </Link>

      <div className="flex items-center gap-2">
        {isAuthenticated ? (
          <>
            <Link to="/create">
              <Button variant="secondary" size="sm" className="flex items-center gap-1">
                <Plus className="w-4 h-4" />
                Создать
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
            <Button size="sm">Войти</Button>
          </Link>
        )}
      </div>
    </header>
  );
}
