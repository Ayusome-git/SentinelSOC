"use client"

import { useState, useEffect, useCallback, useMemo } from "react"
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
import { SeverityBadge } from "@/components/ui/SeverityBadge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { AlertCircle, ShieldAlert, CheckCircle2, XCircle, Search, Filter, Loader2, ChevronDown, Flame } from "lucide-react"

import { alertsApi } from "@/lib/api/alerts"
import { Alert, AlertSummary } from "@/lib/types/alert"
import Link from "next/link"
import { format } from "date-fns"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"


export default function AlertsPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [summary, setSummary] = useState<AlertSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)

  // Filters from URL
  const page = parseInt(searchParams.get("page") || "1")
  const status = searchParams.get("status") || "ALL"
  const risk_level = searchParams.get("risk_level") || "ALL"
  const search = searchParams.get("search") || ""
  const view = searchParams.get("view") || "triage" // triage or all
  
  // Bulk selection
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [bulkActionLoading, setBulkActionLoading] = useState(false)

  const fetchAlerts = useCallback(async () => {
    setLoading(true)
    try {
      const params: any = { page, page_size: 25 }
      
      if (search) params.search = search
      if (status !== "ALL") params.status = status
      if (risk_level !== "ALL") params.risk_level = risk_level
      
      if (view === "triage") {
        params.sort_by = "risk_score"
        params.sort_dir = "desc"
      } else {
        params.sort_by = "detected_at"
        params.sort_dir = "desc"
      }

      const res = await alertsApi.getAlerts(params)
      setAlerts(res.items)
      setTotal(res.total)

      const sumRes = await alertsApi.getSummary()
      setSummary(sumRes)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [page, status, risk_level, search, view])

  useEffect(() => {
    fetchAlerts()
    
    // Auto-refresh the alerts page every 10 seconds so the demo is seamless!
    const interval = setInterval(() => {
      fetchAlerts()
    }, 10000)
    
    return () => clearInterval(interval)
  }, [fetchAlerts])

  const updateFilters = (key: string, value: string | null) => {
    const params = new URLSearchParams(searchParams.toString())
    if (value && value !== "ALL") {
      params.set(key, value)
    } else {
      params.delete(key)
    }
    if (key !== "page") params.set("page", "1")
    router.push(`/alerts?${params.toString()}`)
  }

  const toggleSelection = (id: string) => {
    const next = new Set(selectedIds)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setSelectedIds(next)
  }

  const toggleAll = () => {
    if (selectedIds.size === alerts.length) setSelectedIds(new Set())
    else setSelectedIds(new Set(alerts.map(a => a.id)))
  }

  const handleBulkAction = async (action: 'ACKNOWLEDGE' | 'ASSIGN' | 'RESOLVE' | 'FALSE_POSITIVE') => {
    if (selectedIds.size === 0) return
    setBulkActionLoading(true)
    try {
      await alertsApi.bulkAction(Array.from(selectedIds), action)
      setSelectedIds(new Set())
      await fetchAlerts()
    } catch (err) {
      console.error(err)
      alert("Failed to execute bulk action")
    } finally {
      setBulkActionLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Alert Management" 
        description="SOC Analyst queue for investigating and resolving security threats."
      />
      
      {/* Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Open</CardTitle>
            <AlertCircle className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{summary?.open ?? '-'}</div>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Acknowledged</CardTitle>
            <ShieldAlert className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{summary?.acknowledged ?? '-'}</div>
          </CardContent>
        </Card>
        <Card className="bg-red-950/20 border-red-900/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-red-400">Critical Risk</CardTitle>
            <Flame className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">{summary?.critical ?? '-'}</div>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Unassigned</CardTitle>
            <AlertCircle className="h-4 w-4 text-zinc-500" />
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
              placeholder="Search alerts..."
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
              <SelectItem value="ACKNOWLEDGED">Acknowledged</SelectItem>
              <SelectItem value="RESOLVED">Resolved</SelectItem>
              <SelectItem value="FALSE_POSITIVE">False Positive</SelectItem>
            </SelectContent>
          </Select>
          <Select value={risk_level} onValueChange={(val) => updateFilters("risk_level", val)}>
            <SelectTrigger className="w-[150px] bg-zinc-900 border-zinc-800 text-white">
              <SelectValue placeholder="Risk Level" />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-800 text-white">
              <SelectItem value="ALL">All Risks</SelectItem>
              <SelectItem value="CRITICAL">Critical</SelectItem>
              <SelectItem value="HIGH">High</SelectItem>
              <SelectItem value="MODERATE">Moderate</SelectItem>
              <SelectItem value="LOW">Low</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-2 bg-zinc-900 p-1 rounded-md border border-zinc-800">
          <Button 
            variant={view === "triage" ? "secondary" : "ghost"} 
            size="sm" 
            onClick={() => updateFilters("view", "triage")}
            className={view === "triage" ? "bg-zinc-800" : ""}
          >
            Triage View
          </Button>
          <Button 
            variant={view === "all" ? "secondary" : "ghost"} 
            size="sm"
            onClick={() => updateFilters("view", "all")}
            className={view === "all" ? "bg-zinc-800" : ""}
          >
            All Alerts
          </Button>
        </div>
      </div>

      {/* Bulk Actions Bar */}
      {selectedIds.size > 0 && (
        <div className="flex items-center justify-between p-3 bg-blue-950/40 border border-blue-900/50 rounded-md">
          <div className="text-sm font-medium text-blue-200">
            {selectedIds.size} alert(s) selected
          </div>
          <div className="flex items-center gap-2">
            <DropdownMenu>
              <DropdownMenuTrigger>
                <Button size="sm" variant="outline" className="border-blue-900/50 hover:bg-blue-900/30">
                  Bulk Actions <ChevronDown className="ml-2 h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="bg-zinc-900 border-zinc-800 text-white">
                <DropdownMenuItem onClick={() => handleBulkAction('ACKNOWLEDGE')} disabled={bulkActionLoading}>
                  Acknowledge Selected
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleBulkAction('RESOLVE')} disabled={bulkActionLoading}>
                  Resolve Selected
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleBulkAction('FALSE_POSITIVE')} disabled={bulkActionLoading} className="text-red-400 focus:text-red-400">
                  Mark as False Positive
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="rounded-md border border-zinc-800 bg-zinc-900">
        <Table>
          <TableHeader className="bg-zinc-950/50">
            <TableRow className="border-zinc-800 hover:bg-transparent">
              <TableHead className="w-[40px] text-zinc-400 text-center">
                <Checkbox 
                  checked={alerts.length > 0 && selectedIds.size === alerts.length} 
                  onCheckedChange={toggleAll}
                  aria-label="Select all"
                  className="border-zinc-700 data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600"
                />
              </TableHead>
              <TableHead className="text-zinc-400">Priority (Risk)</TableHead>
              <TableHead className="text-zinc-400">Alert</TableHead>
              <TableHead className="text-zinc-400">Status</TableHead>
              <TableHead className="text-zinc-400">Assigned</TableHead>
              <TableHead className="text-zinc-400">Detected</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              Array(5).fill(0).map((_, i) => (
                <TableRow key={i} className="border-zinc-800 hover:bg-transparent">
                  <TableCell><Skeleton className="h-4 w-4" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-[100px]" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-[250px]" /></TableCell>
                  <TableCell><Skeleton className="h-6 w-[100px] rounded-full" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-[80px]" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-[120px]" /></TableCell>
                </TableRow>
              ))
            ) : alerts.length === 0 ? (
              <TableRow className="border-zinc-800 hover:bg-zinc-800/50">
                <TableCell colSpan={6} className="h-32 text-center text-zinc-500">
                  No alerts match your criteria.
                </TableCell>
              </TableRow>
            ) : (
              alerts.map(alert => (
                <TableRow key={alert.id} className="border-zinc-800 hover:bg-zinc-800/50">
                  <TableCell className="text-center">
                    <Checkbox 
                      checked={selectedIds.has(alert.id)}
                      onCheckedChange={() => toggleSelection(alert.id)}
                      aria-label="Select alert"
                      className="border-zinc-700 data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600"
                    />
                  </TableCell>
                  <TableCell>
                    {alert.risk_level ? (
                      <div className="flex flex-col">
                        <span className={`font-bold ${
                          alert.risk_level === 'CRITICAL' ? 'text-red-500' :
                          alert.risk_level === 'HIGH' ? 'text-orange-500' :
                          alert.risk_level === 'MODERATE' ? 'text-amber-500' : 'text-emerald-500'
                        }`}>{alert.risk_level}</span>
                        <span className="text-xs text-zinc-500">Score: {alert.risk_score}</span>
                      </div>
                    ) : (
                      <SeverityBadge severity={alert.severity} />
                    )}
                  </TableCell>
                  <TableCell>
                    <Link href={`/alerts/${alert.id}`} className="font-medium hover:underline block text-zinc-200">
                      {alert.title}
                    </Link>
                    {alert.description && (
                      <span className="text-xs text-zinc-500 block truncate max-w-md">{alert.description}</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge variant={
                      alert.status === 'OPEN' ? 'destructive' : 
                      alert.status === 'ACKNOWLEDGED' ? 'warning' : 
                      alert.status === 'RESOLVED' ? 'outline' : 'secondary'
                    }>{alert.status}</Badge>
                  </TableCell>
                  <TableCell>
                    {alert.assigned_to ? (
                      <span className="text-sm text-zinc-300">Assigned</span>
                    ) : (
                      <span className="text-sm text-zinc-600 italic">Unassigned</span>
                    )}
                  </TableCell>
                  <TableCell className="text-zinc-400 whitespace-nowrap">
                    {format(new Date(alert.detected_at.endsWith('Z') || alert.detected_at.includes('+') ? alert.detected_at : alert.detected_at + 'Z'), 'MMM d, HH:mm')}
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
