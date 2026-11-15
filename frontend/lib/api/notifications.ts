import { api } from '../api';
import { NotificationListResponse, Notification, NotificationPreference, NotificationPreferenceUpdate } from '../types/notification';

export const getNotifications = async (
  page: number = 1,
  size: number = 50,
  isRead?: boolean
): Promise<NotificationListResponse> => {
  const query = new URLSearchParams({
    page: page.toString(),
    size: size.toString(),
  });
  
  if (isRead !== undefined) {
    query.append('is_read', isRead.toString());
  }

  return api.get(`/api/v1/notifications?${query.toString()}`);
};

export const markNotificationRead = async (id: string): Promise<Notification> => {
  return api.post(`/api/v1/notifications/${id}/read`);
};

export const markAllNotificationsRead = async (): Promise<{status: string}> => {
  return api.post('/api/v1/notifications/read-all');
};

export const getNotificationPreferences = async (): Promise<NotificationPreference> => {
  return api.get('/api/v1/notifications/preferences');
};

export const updateNotificationPreferences = async (
  updates: NotificationPreferenceUpdate
): Promise<NotificationPreference> => {
  return api.put('/api/v1/notifications/preferences', updates);
};
