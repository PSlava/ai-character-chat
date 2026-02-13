import { useEffect, useRef, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { AgeGate } from '@/components/ui/AgeGate';

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const mainRef = useRef<HTMLElement>(null);
  const { pathname } = useLocation();

  useEffect(() => {
    mainRef.current?.scrollTo(0, 0);
  }, [pathname]);

  return (
    <div className="h-screen flex flex-col">
      <Header onToggleSidebar={() => setSidebarOpen((v) => !v)} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <main ref={mainRef} className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
      <AgeGate />
    </div>
  );
}
