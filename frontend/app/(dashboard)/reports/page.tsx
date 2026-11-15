"use client";

import { useState, useEffect } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { getSecurityOverview, exportSecurityOverview } from "@/lib/api/reports";
import { SecurityOverviewReport, ReportFilters } from "@/lib/types/report";
import { applicationsApi } from "@/lib/api/applications";
import { Application } from "@/lib/types/application";
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Legend 
} from "recharts";
import { FileText, Download, Shield, AlertTriangle, Crosshair, CheckCircle2 } from "lucide-react";
import Link from "next/link";

export default function ReportsPage() {
  const [report, setReport] = useState<SecurityOverviewReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [applications, setApplications] = useState<Application[]>([]);
  
  const [timeRange, setTimeRange] = useState<string>("24h");
  const [appId, setAppId] = useState<string>("");
  const [exportingPdf, setExportingPdf] = useState(false);
  const [exportingCsv, setExportingCsv] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    applicationsApi.list({ page_size: 100 }).then(res => setApplications(res.items)).catch(console.error);
  }, []);

  const fetchReport = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const now = new Date();
      let start = new Date();
      
      if (timeRange === "15m") start.setMinutes(now.getMinutes() - 15);
      else if (timeRange === "1h") start.setHours(now.getHours() - 1);
      else if (timeRange === "6h") start.setHours(now.getHours() - 6);
      else if (timeRange === "24h") start.setHours(now.getHours() - 24);
      else if (timeRange === "7d") start.setDate(now.getDate() - 7);
      else if (timeRange === "30d") start.setDate(now.getDate() - 30);
      
      const params: any = {
        start_date: start.toISOString(),
        end_date: now.toISOString(),
      };
      
      if (appId) params.application_id = appId;
      
      const res = await getSecurityOverview(params);
      setReport(res);
    } catch (e: any) {
      setError(e.message || "Failed to load report");
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [timeRange, appId]);

  const handleExport = async (format: 'pdf' | 'csv') => {
    try {
      if (format === 'pdf') setExportingPdf(true);
      else setExportingCsv(true);
      
      const now = new Date();
      let start = new Date();
      if (timeRange === "15m") start.setMinutes(now.getMinutes() - 15);
      else if (timeRange === "1h") start.setHours(now.getHours() - 1);
      else if (timeRange === "6h") start.setHours(now.getHours() - 6);
      else if (timeRange === "24h") start.setHours(now.getHours() - 24);
      else if (timeRange === "7d") start.setDate(now.getDate() - 7);
      else if (timeRange === "30d") start.setDate(now.getDate() - 30);
      
      const params: any = {
        start_date: start.toISOString(),
        end_date: now.toISOString(),
      };
      if (appId) params.application_id = appId;
      
      const blob = await exportSecurityOverview(params, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `security_overview_${now.toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (e) {
      console.error(`Failed to export ${format}:`, e);
      alert(`Failed to export report as ${format.toUpperCase()}`);
    } finally {
      setExportingPdf(false);
      setExportingCsv(false);
    }
  };

  const trendData = report?.trends.events.map(e => {
    const alertPoint = report.trends.alerts.find(a => a.timestamp === e.timestamp);
    const incidentPoint = report.trends.incidents.find(i => i.timestamp === e.timestamp);
    
    // Format timestamp for display depending on range
    let label = new Date(e.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    if (timeRange === "7d" || timeRange === "30d") {
      label = new Date(e.timestamp).toLocaleDateString();
    }
    
    return {
      name: label,
      Events: e.count,
      Alerts: alertPoint?.count || 0,
      Incidents: incidentPoint?.count || 0
    };
  }) || [];

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <PageHeader 
          title="Security Reports" 
          description="Analyze security activity, detections, incidents, risk, and response performance."
        />
        
        <div className="flex gap-2 w-full sm:w-auto">
          <button 
            onClick={() => handleExport('csv')}
            disabled={exportingCsv || loading}
            className="flex items-center gap-2 rounded-md bg-zinc-800 px-3 py-2 text-sm font-semibold text-white hover:bg-zinc-700 disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            {exportingCsv ? "Exporting..." : "CSV"}
          </button>
          <button 
            onClick={() => handleExport('pdf')}
            disabled={exportingPdf || loading}
            className="flex items-center gap-2 rounded-md bg-zinc-800 px-3 py-2 text-sm font-semibold text-white hover:bg-zinc-700 disabled:opacity-50"
          >
            <FileText className="h-4 w-4" />
            {exportingPdf ? "Exporting..." : "PDF"}
          </button>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-4 p-4 bg-[#0f0f11] border border-zinc-800 rounded-lg">
        <div className="flex flex-col gap-1.5 w-full sm:w-48">
          <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Report Type</label>
          <select className="bg-zinc-900 border border-zinc-800 rounded-md text-sm text-zinc-200 px-3 py-2 focus:ring-1 focus:ring-primary focus:outline-none">
            <option value="overview">Security Overview</option>
          </select>
        </div>
        
        <div className="flex flex-col gap-1.5 w-full sm:w-48">
          <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Time Range</label>
          <select 
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="bg-zinc-900 border border-zinc-800 rounded-md text-sm text-zinc-200 px-3 py-2 focus:ring-1 focus:ring-primary focus:outline-none"
          >
            <option value="15m">Last 15 minutes</option>
            <option value="1h">Last 1 hour</option>
            <option value="6h">Last 6 hours</option>
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
          </select>
        </div>
        
        <div className="flex flex-col gap-1.5 w-full sm:w-64">
          <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">Application</label>
          <select 
            value={appId}
            onChange={(e) => setAppId(e.target.value)}
            className="bg-zinc-900 border border-zinc-800 rounded-md text-sm text-zinc-200 px-3 py-2 focus:ring-1 focus:ring-primary focus:outline-none"
          >
            <option value="">All Applications</option>
            {applications.map(app => (
              <option key={app.id} value={app.id}>{app.name}</option>
            ))}
          </select>
        </div>
        
        <div className="flex items-end flex-1 justify-end">
          <button 
            onClick={fetchReport}
            disabled={loading}
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white hover:bg-primary-dark disabled:opacity-50"
          >
            {loading ? "Generating..." : "Generate Report"}
          </button>
        </div>
      </div>

      {error ? (
        <div className="p-8 text-center border border-red-500/20 bg-red-500/10 rounded-lg text-red-400">
          <AlertTriangle className="h-8 w-8 mx-auto mb-3 opacity-80" />
          <p>{error}</p>
        </div>
      ) : loading ? (
        <div className="p-12 text-center text-zinc-500">
          Generating report...
        </div>
      ) : report ? (
        <div className="space-y-6 animate-in fade-in duration-500">
          {/* Executive Summary */}
          <div className="bg-[#0f0f11] border border-zinc-800 rounded-lg p-6">
            <h3 className="text-base font-semibold text-zinc-100 mb-4">Executive Summary</h3>
            <p className="text-sm text-zinc-400 leading-relaxed">
              During the selected period, SentinelSOC recorded <span className="text-zinc-200 font-medium">{report.summary.total_events.toLocaleString()}</span> security events
              {appId ? ` for the selected application` : ` across monitored applications`}. 
              The platform generated <span className="text-zinc-200 font-medium">{report.summary.total_alerts.toLocaleString()}</span> alerts, 
              including <span className="text-red-400 font-medium">{report.summary.critical_alerts}</span> critical alerts.
              {report.summary.open_incidents > 0 ? (
                ` There are ${report.summary.open_incidents} incidents currently open and requiring attention.`
              ) : (
                ` No incidents are currently open.`
              )}
              {report.summary.average_alert_risk !== null && (
                ` The average alert risk score was ${Math.round(report.summary.average_alert_risk)}/100.`
              )}
            </p>
          </div>

          {/* KPI Row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
            <div className="bg-[#0f0f11] border border-zinc-800 rounded-lg p-5 flex flex-col justify-between">
              <span className="text-xs font-medium text-zinc-500 uppercase">Total Events</span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-zinc-100">{report.summary.total_events.toLocaleString()}</span>
              </div>
            </div>
            
            <div className="bg-[#0f0f11] border border-zinc-800 rounded-lg p-5 flex flex-col justify-between">
              <span className="text-xs font-medium text-zinc-500 uppercase">Critical Events</span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-red-500">{report.summary.critical_events.toLocaleString()}</span>
              </div>
            </div>
            
            <div className="bg-[#0f0f11] border border-zinc-800 rounded-lg p-5 flex flex-col justify-between">
              <span className="text-xs font-medium text-zinc-500 uppercase">Active Alerts</span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-orange-400">{report.summary.open_alerts.toLocaleString()}</span>
                {report.summary.critical_alerts > 0 && (
                  <span className="text-xs font-medium text-red-400">({report.summary.critical_alerts} Critical)</span>
                )}
              </div>
            </div>
            
            <div className="bg-[#0f0f11] border border-zinc-800 rounded-lg p-5 flex flex-col justify-between">
              <span className="text-xs font-medium text-zinc-500 uppercase">Open Incidents</span>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-zinc-100">{report.summary.open_incidents.toLocaleString()}</span>
                {report.summary.critical_incidents > 0 && (
                  <span className="text-xs font-medium text-red-400">({report.summary.critical_incidents} Critical)</span>
                )}
              </div>
            </div>
            
            <div className="bg-[#0f0f11] border border-zinc-800 rounded-lg p-5 flex flex-col justify-between">
              <span className="text-xs font-medium text-zinc-500 uppercase">Average Risk</span>
              <div className="mt-2 flex items-baseline gap-2">
                {report.summary.average_alert_risk !== null ? (
                  <span className="text-2xl font-bold text-zinc-100">{Math.round(report.summary.average_alert_risk)}<span className="text-sm text-zinc-500 font-normal">/100</span></span>
                ) : (
                  <span className="text-lg font-medium text-zinc-500">No data</span>
                )}
              </div>
            </div>
            
            <div className="bg-[#0f0f11] border border-zinc-800 rounded-lg p-5 flex flex-col justify-between">
              <span className="text-xs font-medium text-zinc-500 uppercase">Response Success</span>
              <div className="mt-2 flex items-baseline gap-2">
                {report.summary.total_response_actions > 0 ? (
                  <span className="text-2xl font-bold text-zinc-100">
                    {Math.round((report.summary.successful_response_actions / report.summary.total_response_actions) * 100)}%
                  </span>
                ) : (
                  <span className="text-lg font-medium text-zinc-500">No actions</span>
                )}
              </div>
            </div>
          </div>
          
          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-[#0f0f11] border border-zinc-800 rounded-lg p-6">
              <h3 className="text-base font-semibold text-zinc-100 mb-6">Security Activity Trend</h3>
              <div className="h-[300px] w-full">
                {trendData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trendData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                      <XAxis dataKey="name" stroke="#71717a" fontSize={12} tickMargin={10} />
                      <YAxis stroke="#71717a" fontSize={12} tickFormatter={(val) => val >= 1000 ? `${(val/1000).toFixed(1)}k` : val} />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '6px' }}
                        itemStyle={{ fontSize: '13px' }}
                      />
                      <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '20px' }} />
                      <Line type="monotone" dataKey="Events" stroke="#3f3f46" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="Alerts" stroke="#f59e0b" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="Incidents" stroke="#ef4444" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-full items-center justify-center text-sm text-zinc-500">
                    No activity data in this period
                  </div>
                )}
              </div>
            </div>
            
            <div className="bg-[#0f0f11] border border-zinc-800 rounded-lg p-6">
              <h3 className="text-base font-semibold text-zinc-100 mb-6">Severity Distribution (Events)</h3>
              <div className="h-[300px] w-full">
                {report.summary.total_events > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={[
                      { name: 'Critical', value: report.summary.critical_events, fill: '#ef4444' },
                      { name: 'High', value: report.summary.high_events, fill: '#f97316' },
                      { name: 'Medium', value: report.summary.medium_events, fill: '#eab308' },
                      { name: 'Low', value: report.summary.low_events, fill: '#3b82f6' },
                    ]} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={false} />
                      <XAxis type="number" stroke="#71717a" fontSize={12} />
                      <YAxis dataKey="name" type="category" stroke="#71717a" fontSize={12} width={60} />
                      <Tooltip 
                        cursor={{fill: '#27272a', opacity: 0.4}}
                        contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '6px' }}
                      />
                      <Bar dataKey="value" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-full items-center justify-center text-sm text-zinc-500">
                    No events recorded in this period
                  </div>
                )}
              </div>
            </div>
          </div>
          
        </div>
      ) : null}
    </div>
  );
}
