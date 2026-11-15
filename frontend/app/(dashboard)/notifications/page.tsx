"use client";

import { useState, useEffect } from "react";
import { Bell, Check, CheckCircle2, AlertTriangle, AlertCircle, Shield, BrainCircuit, ShieldAlert } from "lucide-react";
import Link from "next/link";
import { getNotifications, markNotificationRead, markAllNotificationsRead } from "@/lib/api/notifications";
import { Notification } from "@/lib/types/notification";
import { PageHeader } from "@/components/layout/PageHeader";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const res = await getNotifications(1, 100); // Fetch up to 100 on page
      setNotifications(res.items);
      setTotal(res.total);
    } catch (e) {
      console.error("Failed to fetch notifications:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const handleMarkRead = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      const notif = await markNotificationRead(id);
      setNotifications(notifications.map(n => n.id === id ? notif : n));
    } catch (e) {
      console.error("Failed to mark as read:", e);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      setNotifications(notifications.map(n => ({ ...n, is_read: true })));
    } catch (e) {
      console.error("Failed to mark all as read:", e);
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'CRITICAL_ALERT':
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      case 'HIGH_RISK_ALERT':
        return <AlertCircle className="h-5 w-5 text-orange-500" />;
      case 'INCIDENT_CREATED':
      case 'INCIDENT_ESCALATED':
        return <ShieldAlert className="h-5 w-5 text-red-400" />;
      case 'INCIDENT_ASSIGNED':
        return <Shield className="h-5 w-5 text-blue-500" />;
      case 'RESPONSE_ACTION_FAILED':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'ML_ANOMALY_DETECTED':
        return <BrainCircuit className="h-5 w-5 text-purple-500" />;
      case 'THREAT_INTELLIGENCE_MATCH':
        return <ShieldAlert className="h-5 w-5 text-red-600" />;
      default:
        return <Bell className="h-5 w-5 text-zinc-500" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <PageHeader 
          title="Notifications" 
          description="View and manage your security notifications"
        />
        <div className="flex gap-4">
          <Link
            href="/settings/notifications"
            className="rounded-md bg-zinc-800 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-zinc-700"
          >
            Preferences
          </Link>
          <button
            onClick={handleMarkAllRead}
            className="rounded-md bg-primary px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary-dark"
          >
            Mark all as read
          </button>
        </div>
      </div>

      <div className="bg-[#0f0f11] border border-zinc-800 rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-zinc-500">Loading notifications...</div>
        ) : notifications.length === 0 ? (
          <div className="p-12 text-center text-zinc-500 flex flex-col items-center">
            <Bell className="h-12 w-12 mb-4 opacity-20" />
            <p>You have no notifications.</p>
          </div>
        ) : (
          <ul className="divide-y divide-zinc-800">
            {notifications.map((notif) => (
              <li 
                key={notif.id} 
                className={`relative p-6 hover:bg-zinc-900/50 transition-colors flex gap-4 ${
                  !notif.is_read ? 'bg-primary/5' : ''
                }`}
              >
                <div className="mt-1 flex-shrink-0">
                  {getIcon(notif.notification_type)}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="text-sm font-semibold text-zinc-100">
                        {notif.title}
                      </h4>
                      <p className="mt-1 text-sm text-zinc-400">
                        {notif.message}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-zinc-500">
                        {new Date(notif.created_at).toLocaleString()}
                      </span>
                      {!notif.is_read && (
                        <button
                          onClick={(e) => handleMarkRead(notif.id, e)}
                          className="text-zinc-500 hover:text-primary transition-colors z-20 relative"
                          title="Mark as read"
                        >
                          <CheckCircle2 className="h-5 w-5" />
                        </button>
                      )}
                    </div>
                  </div>
                  {notif.link_path && (
                    <Link 
                      href={notif.link_path}
                      className="absolute inset-0 z-10"
                    >
                      <span className="sr-only">View notification details</span>
                    </Link>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
