"use client"

import { Search, User, LogOut } from "lucide-react"
import { useAuth } from "@/lib/auth"
import { NotificationBell } from "@/components/notifications/NotificationBell"

export function TopNav() {
  const { user, logout } = useAuth()

  return (
    <header className="flex h-16 items-center justify-between border-b border-zinc-800 bg-[#0a0a0a] px-6">
      <div className="flex flex-1 items-center">
        <div className="relative w-full max-w-md">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
            <Search className="h-4 w-4 text-zinc-500" />
          </div>
          <input
            type="text"
            className="block w-full rounded-md border-0 bg-zinc-900 py-1.5 pl-10 pr-3 text-zinc-300 ring-1 ring-inset ring-zinc-800 placeholder:text-zinc-500 focus:ring-2 focus:ring-inset focus:ring-primary sm:text-sm sm:leading-6"
            placeholder="Search events, alerts..."
            disabled
          />
        </div>
      </div>
      <div className="flex items-center space-x-6">
        <NotificationBell />
        
        {user ? (
          <div className="flex items-center space-x-4 border-l border-zinc-800 pl-6">
            <div className="flex flex-col items-end">
              <span className="text-sm font-medium text-zinc-200">{user.full_name || user.email}</span>
              <span className="text-xs text-zinc-500">{user.role}</span>
            </div>
            <div className="h-9 w-9 rounded-full bg-zinc-800 flex items-center justify-center border border-zinc-700">
              <User className="h-5 w-5 text-zinc-400" />
            </div>
            <button 
              onClick={logout}
              className="text-zinc-500 hover:text-zinc-50 transition-colors ml-2"
              title="Logout"
            >
              <LogOut className="h-5 w-5" />
            </button>
          </div>
        ) : (
          <div className="h-9 w-9 rounded-full bg-zinc-800 flex items-center justify-center border border-zinc-700">
            <User className="h-5 w-5 text-zinc-400" />
          </div>
        )}
      </div>
    </header>
  )
}
