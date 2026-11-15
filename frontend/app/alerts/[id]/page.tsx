"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { PageHeader } from "@/components/layout/PageHeader"
import { alertsApi } from "@/lib/api/alerts"
import { usersApi } from "@/lib/api/users"
import { Alert, AlertComment } from "@/lib/types/alert"
import { User } from "@/lib/types/user"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { SeverityBadge } from "@/components/ui/SeverityBadge"
import { Textarea } from "@/components/ui/textarea"
import { format } from "date-fns"
import Link from "next/link"
import { Loader2, Send, CheckCircle2, AlertTriangle, ShieldCheck, ShieldAlert, User as UserIcon, BrainCircuit } from "lucide-react"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"


export default function AlertDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter()
  
  const [alert, setAlert] = useState<Alert | null>(null)
  const [comments, setComments] = useState<AlertComment[]>([])
  const [users, setUsers] = useState<User[]>([])
  
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  
  const [newComment, setNewComment] = useState("")

  const fetchData = async () => {
    try {
      const [alertData, commentsData, usersData] = await Promise.all([
        alertsApi.getAlert(params.id),
        alertsApi.getComments(params.id),
        usersApi.getUsers()
      ])
      setAlert(alertData)
      setComments(commentsData)
      setUsers(usersData.items.filter(u => u.is_active))
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [params.id])

  const handleAction = async (action: 'acknowledge' | 'resolve' | 'falsePositive') => {
    setActionLoading(true)
    try {
      if (action === 'acknowledge') await alertsApi.acknowledge(params.id)
      if (action === 'resolve') await alertsApi.resolve(params.id)
      if (action === 'falsePositive') await alertsApi.markFalsePositive(params.id)
      await fetchData()
    } catch (err) {
      console.error(err)
    } finally {
      setActionLoading(false)
    }
  }

  const handleCreateIncident = async () => {
    setActionLoading(true)
    try {
      const res = await alertsApi.createIncident(params.id)
      try {
        router.push(`/incidents/${res.incident_id}`)
      } catch (navErr) {
        window.location.href = `/incidents/${res.incident_id}`
      }
    } catch (err) {
      console.error(err)
      window.alert(`Failed to create incident: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setActionLoading(false)
    }
  }

  const handleAssign = async (userId: string | null) => {
    setActionLoading(true)
    try {
      await alertsApi.assign(params.id, userId === "unassigned" || userId === null ? null : userId)
      await fetchData()
    } catch (err) {
      console.error(err)
    } finally {
      setActionLoading(false)
    }
  }

  const handleAddComment = async () => {
    if (!newComment.trim()) return
    setActionLoading(true)
    try {
      await alertsApi.addComment(params.id, newComment)
      setNewComment("")
      await fetchData()
    } catch (err) {
      console.error(err)
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin h-8 w-8 text-zinc-500" /></div>
  if (!alert) return <div className="p-8 text-red-500">Alert not found.</div>

  const isTerminal = alert.status === "RESOLVED" || alert.status === "FALSE_POSITIVE"

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <PageHeader 
          title={alert.title}
          description={`Detected at ${format(new Date(alert.detected_at), 'MMM d, yyyy HH:mm:ss')}`}
        />
        
        {/* Action Bar */}
        <div className="flex items-center gap-2 flex-wrap">
          <Button
            variant="default"
            size="sm"
            onClick={handleCreateIncident}
            disabled={actionLoading}
            className="bg-blue-600 hover:bg-blue-700"
          >
            Create Incident
          </Button>
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => handleAction('acknowledge')}
            disabled={alert.status !== "OPEN" || actionLoading || isTerminal}
            className="border-amber-900/50 text-amber-500 hover:bg-amber-900/20"
          >
            <ShieldCheck className="h-4 w-4 mr-2" /> Acknowledge
          </Button>
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => handleAction('resolve')}
            disabled={actionLoading || isTerminal}
            className="border-emerald-900/50 text-emerald-500 hover:bg-emerald-900/20"
          >
            <CheckCircle2 className="h-4 w-4 mr-2" /> Resolve
          </Button>
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => handleAction('falsePositive')}
            disabled={actionLoading || isTerminal}
            className="border-zinc-800 text-zinc-400 hover:bg-zinc-800"
          >
            <AlertTriangle className="h-4 w-4 mr-2" /> False Positive
          </Button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader className="flex flex-row justify-between items-center pb-2">
              <CardTitle>Alert Summary</CardTitle>
              <Badge variant={
                alert.status === 'OPEN' ? 'destructive' : 
                alert.status === 'ACKNOWLEDGED' ? 'warning' : 
                alert.status === 'RESOLVED' ? 'outline' : 'secondary'
              }>{alert.status}</Badge>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-zinc-500 text-sm">Description</span>
                  <p className="mt-1 text-zinc-300">{alert.description || 'No description provided.'}</p>
                </div>
                <div>
                  <span className="text-zinc-500 text-sm">Application ID</span>
                  <p className="mt-1 text-zinc-300 font-mono text-sm">{alert.application_id}</p>
                </div>
              </div>

              <div className="pt-4 border-t border-zinc-800">
                <h3 className="text-sm font-medium text-zinc-400 mb-2">Detection Explanation</h3>
                <div className="p-4 bg-zinc-950 rounded-md border border-zinc-800">
                  <p className="text-zinc-300 text-sm">
                    {alert.detection_source === "ML" 
                      ? "This alert was generated by the Machine Learning Anomaly Detection Engine because application behavior deviated significantly from learned baselines."
                      : alert.correlation_id 
                        ? "This alert was generated by the Event Correlation Engine because a sequence of events matched a defined correlation rule indicating a composite attack."
                        : "This alert was generated by the Rule-Based Detection Engine because a security event matched a configured detection rule."}
                  </p>
                </div>
              </div>

              {alert.threat_intel_indicators && alert.threat_intel_indicators.length > 0 && (
                <div className="pt-4 border-t border-zinc-800">
                  <h3 className="text-sm font-medium text-zinc-400 mb-2">Threat Intelligence Insights</h3>
                  <div className="space-y-2">
                    {alert.threat_intel_indicators.map((ti: any) => (
                      <div key={ti.id} className="p-3 bg-zinc-950 rounded-md border border-zinc-800 flex justify-between items-center">
                        <div>
                          <div className="flex items-center space-x-2">
                            {ti.malicious ? <ShieldAlert className="h-4 w-4 text-destructive" /> : <ShieldCheck className="h-4 w-4 text-emerald-500" />}
                            <span className="font-mono text-sm text-zinc-200">{ti.indicator}</span>
                            <Badge variant="outline" className="text-[10px] py-0">{ti.indicator_type}</Badge>
                          </div>
                          <div className="text-xs text-zinc-500 mt-1">Source: {ti.source}</div>
                        </div>
                        <Badge variant={ti.malicious ? "destructive" : "secondary"}>
                          Confidence: {ti.confidence}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Comments Section */}
          <Card className="bg-zinc-900 border-zinc-800 flex flex-col h-[500px]">
            <CardHeader>
              <CardTitle>Analyst Investigation Notes</CardTitle>
              <CardDescription>Append-only audit trail of analyst findings.</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col min-h-0">
              <div className="flex-1 overflow-y-auto space-y-4 pr-2 mb-4">
                {comments.length === 0 ? (
                  <div className="text-center text-zinc-500 py-8">No comments yet.</div>
                ) : (
                  comments.map(comment => (
                    <div key={comment.id} className="p-3 bg-zinc-950 rounded-md border border-zinc-800">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-blue-400 flex items-center gap-2">
                          <UserIcon className="h-3 w-3" />
                          {users.find(u => u.id === comment.user_id)?.full_name || comment.user_id}
                        </span>
                        <span className="text-xs text-zinc-500">
                          {format(new Date(comment.created_at), 'MMM d, HH:mm')}
                        </span>
                      </div>
                      <p className="text-sm text-zinc-300 whitespace-pre-wrap">{comment.comment}</p>
                    </div>
                  ))
                )}
              </div>
              
              <div className="mt-auto">
                <Textarea 
                  placeholder="Add a note to the investigation..." 
                  className="bg-zinc-950 border-zinc-800 resize-none h-24 mb-2"
                  value={newComment}
                  onChange={e => setNewComment(e.target.value)}
                />
                <Button 
                  className="w-full" 
                  onClick={handleAddComment}
                  disabled={actionLoading || !newComment.trim()}
                >
                  <Send className="h-4 w-4 mr-2" /> Submit Note
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <CardTitle>Assignment</CardTitle>
            </CardHeader>
            <CardContent>
              <Select 
                value={alert.assigned_to || "unassigned"} 
                onValueChange={handleAssign}
                disabled={actionLoading}
              >
                <SelectTrigger className="w-full bg-zinc-950 border-zinc-800 text-white">
                  <SelectValue placeholder="Select assignee" />
                </SelectTrigger>
                <SelectContent className="bg-zinc-950 border-zinc-800 text-white">
                  <SelectItem value="unassigned" className="italic text-zinc-500">Unassigned</SelectItem>
                  {users.map(u => (
                    <SelectItem key={u.id} value={u.id}>{u.full_name || u.email}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <CardTitle>Risk & Priority</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <span className="text-zinc-500 text-sm">Severity</span>
                <p className="mt-1">
                  <SeverityBadge severity={alert.severity} className="text-sm px-3 py-1" />
                </p>
              </div>
              
              <div className="pt-4 border-t border-zinc-800">
                <span className="text-zinc-500 text-sm">Risk Score</span>
                <div className="flex items-center gap-3 mt-1">
                  <span className="text-3xl font-bold">{alert.risk_score || 0}</span>
                  <span className="text-zinc-500">/ 100</span>
                  {alert.risk_level && (
                    <Badge variant={
                      alert.risk_level === 'CRITICAL' ? 'destructive' :
                      alert.risk_level === 'HIGH' ? 'destructive' :
                      alert.risk_level === 'MODERATE' ? 'warning' : 'secondary'
                    }>{alert.risk_level}</Badge>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {alert.risk_factors && (
            <Card className="bg-zinc-900 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                  Why this score?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(alert.risk_factors).map(([factor, score]) => (
                    <div key={factor} className="flex items-center justify-between">
                      <span className="text-zinc-300 capitalize">{factor.replace('_', ' ')}</span>
                      <span className="font-mono text-zinc-400">+{score}</span>
                    </div>
                  ))}
                  <div className="pt-3 mt-3 border-t border-zinc-800 flex items-center justify-between font-medium">
                    <span>Final Risk Score</span>
                    <span>{alert.risk_score}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <CardTitle>Security Evidence</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {alert.correlation_id ? (
                <div>
                  <p className="text-sm text-zinc-400 mb-2">This alert originated from a correlated sequence.</p>
                  <Link href={`/correlations/${alert.correlation_id}`} className="inline-flex shrink-0 items-center justify-center rounded-lg border border-border bg-background text-sm font-medium hover:bg-muted hover:text-foreground w-full h-8 px-2.5">
                    View Correlated Sequence
                  </Link>
                </div>
              ) : alert.security_event_id ? (
                <div>
                  <p className="text-sm text-zinc-400 mb-2">This alert originated from a single detection event.</p>
                  <Link href={`/events/${alert.security_event_id}`} className="inline-flex shrink-0 items-center justify-center rounded-lg border border-border bg-background text-sm font-medium hover:bg-muted hover:text-foreground w-full h-8 px-2.5">
                    View Triggering Event
                  </Link>
                </div>
              ) : (
                <p className="text-sm text-zinc-500">No direct evidence linked.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
