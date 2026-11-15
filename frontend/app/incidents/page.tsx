"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { PageHeader } from "@/components/layout/PageHeader"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { SeverityBadge } from "@/components/ui/SeverityBadge"
import { RiskBadge } from "@/components/ui/RiskBadge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Shield, AlertTriangle, AlertCircle, Search, Loader2, Flame, CheckCircle2 } from "lucide-react"

import { incidentsApi } from "@/lib/api/incidents"
import { IncidentSummary } from "@/lib/types/incident"
import Link from "next/link"
import { format } from "date-fns"

export default function IncidentsPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  
  const [incidents, setIncidents] = useState<any[]>([])
  const [summary, setSummary] = useState<IncidentSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)

  // Filters from URL
  const page = parseInt(searchParams.get("page") || "1")
  const status = searchParams.get("status") || "ALL"
  const severity = searchParams.get("severity") || "ALL"
  const search = searchParams.get("search") || ""

  const fetchIncidents = useCallback(async () => {
    setLoading(true)
    try {
      const params: any = { page, size: 25 }
      
      if (search) params.search = search
      if (status !== "ALL") params.status = status
      if (severity !== "ALL") params.severity = severity

      const res = await incidentsApi.getIncidents(params)
      setIncidents(res.items)
      setTotal(res.total)

      const sumRes = await incidentsApi.getSummary()
      setSummary(sumRes)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [page, status, severity, search])

  useEffect(() => {
    fetchIncidents()
  }, [fetchIncidents])

  const updateFilters = (key: string, value: string | null) => {
    const params = new URLSearchParams(searchParams.toString())
    if (value && value !== "ALL") {
      params.set(key, value)
    } else {
      params.delete(key)
    }
    if (key !== "page") params.set("page", "1")
    router.push(`/incidents?${params.toString()}`)
  }

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Incident Management" 
        description="SOC Analyst queue for investigating and resolving security incidents."
      />
      
      {/* Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Open & Investigating</CardTitle>
            <AlertCircle className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{(summary?.open || 0) + (summary?.investigating || 0)}</div>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Contained</CardTitle>
            <Shield className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{summary?.contained ?? '-'}</div>
          </CardContent>
        </Card>
        <Card className="bg-red-950/20 border-red-900/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-red-400">Critical Incidents</CardTitle>
            <Flame className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">{summary?.critical ?? '-'}</div>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Unassigned</CardTitle>
            <AlertTriangle className="h-4 w-4 text-zinc-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{summary?.unassigned ?? '-'}</div>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Avg Risk</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{summary ? Math.round(summary.average_risk_score) : '-'}</div>
          </CardContent>
        </Card>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-zinc-500" />
            <Input
              type="text"
              placeholder="Search incidents..."
              className="pl-9 w-[250px] bg-zinc-900 border-zinc-800 text-white"
              value={search}
              onChange={(e) => updateFilters("search", e.target.value)}
            />
          </div>
          <Select value={status} onValueChange={(val) => updateFilters("status", val)}>
            <SelectTrigger className="w-[150px] bg-zinc-900 border-zinc-800 text-white">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-800 text-white">
              <SelectItem value="ALL">All Statuses</SelectItem>
              <SelectItem value="OPEN">Open</SelectItem>
              <SelectItem value="INVESTIGATING">Investigating</SelectItem>
              <SelectItem value="CONTAINED">Contained</SelectItem>
              <SelectItem value="RESOLVED">Resolved</SelectItem>
              <SelectItem value="CLOSED">Closed</SelectItem>
            </SelectContent>
          </Select>
          <Select value={severity} onValueChange={(val) => updateFilters("severity", val)}>
            <SelectTrigger className="w-[150px] bg-zinc-900 border-zinc-800 text-white">
              <SelectValue placeholder="Severity" />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-800 text-white">
              <SelectItem value="ALL">All Severities</SelectItem>
              <SelectItem value="CRITICAL">Critical</SelectItem>
              <SelectItem value="HIGH">High</SelectItem>
              <SelectItem value="MEDIUM">Medium</SelectItem>
              <SelectItem value="LOW">Low</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Table */}
      <div className="rounded-md border border-zinc-800 bg-zinc-900">
        <Table>
          <TableHeader className="bg-zinc-950/50">
            <TableRow className="border-zinc-800 hover:bg-transparent">
              <TableHead className="text-zinc-400">Incident</TableHead>
              <TableHead className="text-zinc-400">Priority</TableHead>
              <TableHead className="text-zinc-400">Status</TableHead>
              <TableHead className="text-zinc-400">Assigned</TableHead>
              <TableHead className="text-zinc-400">Detected</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              Array(5).fill(0).map((_, i) => (
                <TableRow key={i} className="border-zinc-800 hover:bg-transparent">
                  <TableCell><Skeleton className="h-5 w-[250px]" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-[100px]" /></TableCell>
                  <TableCell><Skeleton className="h-6 w-[100px] rounded-full" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-[80px]" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-[120px]" /></TableCell>
                </TableRow>
              ))
            ) : incidents.length === 0 ? (
              <TableRow className="border-zinc-800 hover:bg-zinc-800/50">
                <TableCell colSpan={5} className="h-32 text-center text-zinc-500">
                  No incidents match your criteria.
                </TableCell>
              </TableRow>
            ) : (
              incidents.map(incident => (
                <TableRow key={incident.id} className="border-zinc-800 hover:bg-zinc-800/50">
                  <TableCell>
                    <Link href={`/incidents/${incident.id}`} className="font-medium hover:underline block text-zinc-200">
                      <span className="text-blue-400 font-mono text-sm mr-2">{incident.incident_number}</span>
                      {incident.title}
                    </Link>
                    {incident.description && (
                      <span className="text-xs text-zinc-500 block truncate max-w-md">{incident.description}</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-col">
                        <SeverityBadge severity={incident.severity} />
                        <div className="mt-1">
                          <RiskBadge score={incident.risk_score} />
                        </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={
                      incident.status === 'OPEN' ? 'destructive' : 
                      incident.status === 'INVESTIGATING' ? 'warning' : 
                      incident.status === 'CONTAINED' ? 'secondary' : 
                      incident.status === 'RESOLVED' ? 'outline' : 'default'
                    }>{incident.status}</Badge>
                  </TableCell>
                  <TableCell>
                    {incident.assigned_to ? (
                      <span className="text-sm text-zinc-300">Assigned</span>
                    ) : (
                      <span className="text-sm text-zinc-600 italic">Unassigned</span>
                    )}
                  </TableCell>
                  <TableCell className="text-zinc-400 whitespace-nowrap">
                    {format(new Date(incident.detected_at), 'MMM d, HH:mm')}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {total > 25 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-zinc-500">
            Showing {((page - 1) * 25) + 1} to {Math.min(page * 25, total)} of {total} results
          </p>
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              disabled={page === 1}
              onClick={() => updateFilters("page", String(page - 1))}
              className="border-zinc-800 bg-zinc-900 text-white"
            >
              Previous
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              disabled={page * 25 >= total}
              onClick={() => updateFilters("page", String(page + 1))}
              className="border-zinc-800 bg-zinc-900 text-white"
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
