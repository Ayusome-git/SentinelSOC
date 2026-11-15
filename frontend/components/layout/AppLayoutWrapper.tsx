"use client"

import { usePathname } from 'next/navigation'
import { Sidebar } from "@/components/layout/Sidebar"
import { TopNav } from "@/components/layout/TopNav"
import { ProtectedRoute } from "@/components/auth/ProtectedRoute"
import { Toaster } from 'sonner';

export function AppLayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  
  if (pathname === '/login') {
    return (
      <>
        {children}
        <Toaster theme="dark" position="bottom-right" />
      </>
    )
  }

  return (
    <ProtectedRoute>
      <div className="flex h-screen w-full">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <TopNav />
          <main className="flex-1 overflow-y-auto p-6 lg:p-8">
            {children}
          </main>
        </div>
      </div>
      <Toaster theme="dark" position="bottom-right" />
    </ProtectedRoute>
  )
}
