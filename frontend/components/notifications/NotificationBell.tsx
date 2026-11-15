"use client";

import { useState, useEffect } from "react";
import { Bell, Check, ExternalLink } from "lucide-react";
import Link from "next/link";
import { getNotifications, markNotificationRead } from "@/lib/api/notifications";
import { Notification } from "@/lib/types/notification";

export function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const res = await getNotifications(1, 5, false); // Fetch 5 most recent unread
      setNotifications(res.items);
      setUnreadCount(res.unread_count);
    } catch (e) {
      console.error("Failed to fetch notifications:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
    // In a real app we'd use WebSocket or polling
    const interval = setInterval(fetchNotifications, 60000); // Poll every minute
    return () => clearInterval(interval);
  }, []);

  const handleMarkRead = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await markNotificationRead(id);
      setNotifications(notifications.filter(n => n.id !== id));
      setUnreadCount(Math.max(0, unreadCount - 1));
    } catch (e) {
      console.error("Failed to mark as read:", e);
    }
  };

  return (
    <div className="relative">
      <button 
        className="text-zinc-400 hover:text-zinc-50 transition-colors relative flex items-center justify-center p-2 rounded-md hover:bg-zinc-800"
        onClick={() => {
          setIsOpen(!isOpen);
          if (!isOpen && notifications.length === 0) fetchNotifications();
        }}
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-white ring-2 ring-[#0a0a0a]">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 mt-2 w-80 rounded-md border border-zinc-800 bg-[#0f0f11] shadow-xl z-50 overflow-hidden">
            <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-3 bg-[#131316]">
              <h3 className="text-sm font-medium text-zinc-100">Notifications</h3>
              <Link 
                href="/notifications" 
                className="text-xs text-primary hover:text-primary-light"
                onClick={() => setIsOpen(false)}
              >
                View all
              </Link>
            </div>
            
            <div className="max-h-[300px] overflow-y-auto">
              {loading && notifications.length === 0 ? (
                <div className="px-4 py-6 text-center text-sm text-zinc-500">Loading...</div>
              ) : notifications.length === 0 ? (
                <div className="px-4 py-6 text-center text-sm text-zinc-500">
                  <Bell className="mx-auto h-6 w-6 mb-2 opacity-20" />
                  No new notifications
                </div>
              ) : (
                <div className="divide-y divide-zinc-800/50">
                  {notifications.map((notif) => (
                    <div key={notif.id} className="relative flex flex-col p-4 hover:bg-zinc-800/50 transition-colors group">
                      <div className="flex justify-between items-start mb-1">
                        <span className="text-xs font-medium text-primary">
                          {notif.notification_type.replace(/_/g, ' ')}
                        </span>
                        <button 
                          onClick={(e) => handleMarkRead(notif.id, e)}
                          className="text-zinc-600 hover:text-zinc-300 transition-colors"
                          title="Mark as read"
                        >
                          <Check className="h-3.5 w-3.5" />
                        </button>
                      </div>
                      <p className="text-sm font-medium text-zinc-200 line-clamp-1">{notif.title}</p>
                      <p className="text-xs text-zinc-400 mt-1 line-clamp-2">{notif.message}</p>
                      
                      {notif.link_path && (
                        <Link 
                          href={notif.link_path}
                          onClick={() => setIsOpen(false)}
                          className="absolute inset-0 z-10"
                        >
                          <span className="sr-only">View details</span>
                        </Link>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            <div className="border-t border-zinc-800 bg-[#131316] p-2 text-center">
              <Link 
                href="/settings/notifications" 
                className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
                onClick={() => setIsOpen(false)}
              >
                Notification Preferences
              </Link>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
