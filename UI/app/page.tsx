"use client";

import { AppProvider, useAppContext } from '@/lib/app-context';
import { LaunchPage } from '@/components/launch-page';
import { DashboardPage } from '@/components/dashboard/dashboard-page';

function AppContent() {
  const { currentPage } = useAppContext();

  return currentPage === 'launch' ? <LaunchPage /> : <DashboardPage />;
}

export default function Page() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}
