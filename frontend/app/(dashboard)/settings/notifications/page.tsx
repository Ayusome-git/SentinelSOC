"use client";

import { useState, useEffect } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { getNotificationPreferences, updateNotificationPreferences } from "@/lib/api/notifications";
import { NotificationPreferenceUpdate } from "@/lib/types/notification";

export default function NotificationPreferencesPage() {
  const [preferences, setPreferences] = useState<NotificationPreferenceUpdate>({
    notify_on_critical_alerts: true,
    notify_on_high_risk: true,
    notify_on_incident_assigned: true,
    notify_on_incident_created: true,
    notify_on_incident_escalated: true,
    notify_on_response_failure: true,
    notify_on_ml_anomaly: true,
    notify_on_ti_match: true,
    receive_emails: false,
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

  useEffect(() => {
    const fetchPrefs = async () => {
      try {
        const prefs = await getNotificationPreferences();
        setPreferences({
          notify_on_critical_alerts: prefs.notify_on_critical_alerts,
          notify_on_high_risk: prefs.notify_on_high_risk,
          notify_on_incident_assigned: prefs.notify_on_incident_assigned,
          notify_on_incident_created: prefs.notify_on_incident_created,
          notify_on_incident_escalated: prefs.notify_on_incident_escalated,
          notify_on_response_failure: prefs.notify_on_response_failure,
          notify_on_ml_anomaly: prefs.notify_on_ml_anomaly,
          notify_on_ti_match: prefs.notify_on_ti_match,
          receive_emails: prefs.receive_emails,
        });
      } catch (e) {
        console.error("Failed to load preferences:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchPrefs();
  }, []);

  const handleChange = (key: keyof NotificationPreferenceUpdate, value: boolean) => {
    setPreferences(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setMessage(null);
      await updateNotificationPreferences(preferences);
      setMessage({ type: 'success', text: 'Preferences saved successfully.' });
    } catch (e) {
      console.error("Failed to save preferences:", e);
      setMessage({ type: 'error', text: 'Failed to save preferences.' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-zinc-500">Loading preferences...</div>;
  }

  const sections = [
    {
      title: "Alert & Detection Settings",
      description: "Get notified when important security alerts are generated.",
      items: [
        { key: 'notify_on_critical_alerts', label: 'Critical Alerts', desc: 'Alerts scored 75+ or manually marked as Critical' },
        { key: 'notify_on_high_risk', label: 'High Risk Alerts', desc: 'Alerts scored 50-74' },
        { key: 'notify_on_ml_anomaly', label: 'ML Anomalies', desc: 'Anomalous behavior detected by machine learning' },
        { key: 'notify_on_ti_match', label: 'Threat Intel Matches', desc: 'Known malicious indicators observed in your environment' },
      ]
    },
    {
      title: "Incident Workflow Settings",
      description: "Get notified about incident assignments and escalations.",
      items: [
        { key: 'notify_on_incident_created', label: 'Incident Created', desc: 'When a new incident is created manually or automatically' },
        { key: 'notify_on_incident_assigned', label: 'Incident Assigned', desc: 'When an incident is assigned to you' },
        { key: 'notify_on_incident_escalated', label: 'Incident Escalated', desc: 'When an incident severity is increased' },
      ]
    },
    {
      title: "Response & Automation Settings",
      description: "Get notified about automated response actions.",
      items: [
        { key: 'notify_on_response_failure', label: 'Response Action Failed', desc: 'When an automated or manual response action fails to execute' },
      ]
    },
    {
      title: "Delivery Settings",
      description: "How you want to receive notifications.",
      items: [
        { key: 'receive_emails', label: 'Receive Emails', desc: 'Send a copy of notifications to your email address' },
      ]
    }
  ];

  return (
    <div className="max-w-4xl space-y-8">
      <PageHeader 
        title="Notification Preferences" 
        description="Manage how and when you receive security notifications."
      />

      {message && (
        <div className={`p-4 rounded-md ${message.type === 'success' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
          {message.text}
        </div>
      )}

      <div className="space-y-10">
        {sections.map((section, idx) => (
          <div key={idx} className="border border-zinc-800 rounded-lg overflow-hidden bg-[#0f0f11]">
            <div className="border-b border-zinc-800 px-6 py-5 bg-[#131316]">
              <h3 className="text-base font-semibold text-zinc-100">{section.title}</h3>
              <p className="mt-1 text-sm text-zinc-400">{section.description}</p>
            </div>
            <div className="divide-y divide-zinc-800/50 p-6">
              {section.items.map((item) => (
                <div key={item.key} className="flex items-center justify-between py-4 first:pt-0 last:pb-0">
                  <div className="flex flex-col">
                    <span className="text-sm font-medium text-zinc-200">{item.label}</span>
                    <span className="text-sm text-zinc-500 mt-1">{item.desc}</span>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="sr-only peer" 
                      checked={preferences[item.key as keyof NotificationPreferenceUpdate] as boolean}
                      onChange={(e) => handleChange(item.key as keyof NotificationPreferenceUpdate, e.target.checked)}
                    />
                    <div className="w-11 h-6 bg-zinc-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-zinc-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  </label>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="flex justify-end pt-4">
        <button
          onClick={handleSave}
          disabled={saving}
          className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-dark disabled:opacity-50 flex items-center"
        >
          {saving ? "Saving..." : "Save Preferences"}
        </button>
      </div>
    </div>
  );
}
