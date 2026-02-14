import { useEffect, useRef, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { Footer } from './Footer';
import { AgeGate } from '@/components/ui/AgeGate';
import { trackPageView } from '@/api/analytics';

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const mainRef = useRef<HTMLElement>(null);
  const { pathname } = useLocation();

  useEffect(() => {
    mainRef.current?.scrollTo(0, 0);
    trackPageView(pathname);
  }, [pathname]);

  return (
    <div className="h-screen flex flex-col">
      <Header onToggleSidebar={() => setSidebarOpen((v) => !v)} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <main ref={mainRef} className="flex-1 overflow-y-auto">
          <div className="min-h-full flex flex-col">
            <div className="flex-1">
              <Outlet />
            </div>
            <Footer />
          </div>
        </main>
      </div>
      <AgeGate />
      <Toaster
        position="bottom-center"
        toastOptions={{
          style: { background: '#262626', color: '#f5f5f5', border: '1px solid #404040' },
          duration: 3000,
        }}
      />
    </div>
  );
}
