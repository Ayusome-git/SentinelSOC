"use client"

import { useState, useEffect, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import { PageHeader } from "@/components/layout/PageHeader"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { SeverityBadge } from "@/components/ui/SeverityBadge"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Loader2, ArrowLeft, Shield, Clock, CheckCircle2, Save, FileText, Search, Star, Activity, ArrowRight } from "lucide-react"
import { format } from "date-fns"
import Link from "next/link"

import { incidentsApi } from "@/lib/api/incidents"
import { TimelineEntry, EntitiesResponse, IncidentEvidenceResponse } from "@/lib/types/investigation"
import { TimelineEntry as TimelineEntryComponent } from "@/components/investigation/TimelineEntry"
import { EntitySummary } from "@/components/investigation/EntitySummary"
import { KeyEvidencePanel } from "@/components/investigation/KeyEvidencePanel"
import { ResponseActionsPanel } from "@/components/investigation/ResponseActionsPanel"

export default function InvestigationWorkspace() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string

  const [incident, setIncident] = useState<any>(null)
  const [timeline, setTimeline] = useState<TimelineEntry[]>([])
  const [entities, setEntities] = useState<EntitiesResponse | null>(null)
  
  const [pinnedEvidence, setPinnedEvidence] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  
  const [newComment, setNewComment] = useState("")
  const [addingComment, setAddingComment] = useState(false)
  
  // Timeline Filters
  const [filterTypes, setFilterTypes] = useState<string>("")
  const [searchQuery, setSearchQuery] = useState("")

  // Drawer State
  const [selectedEvent, setSelectedEvent] = useState<TimelineEntry | null>(null)

  const fetchWorkspaceData = useCallback(async () => {
    try {
      const incData = await incidentsApi.getIncident(id)
      setIncident(incData)
      
      const timelineData = await incidentsApi.getTimeline(id, { types: filterTypes, search: searchQuery })
      setTimeline((timelineData.items as any) || [])
      
      const entitiesData = await incidentsApi.getEntities(id)
      setEntities(entitiesData as any)
      
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [id, filterTypes, searchQuery])

  useEffect(() => {
    fetchWorkspaceData()
  }, [fetchWorkspaceData])

  const handleStatusChange = async (newStatus: string) => {
    try {
      await incidentsApi.updateStatus(id, newStatus)
      await fetchWorkspaceData()
    } catch (err) {
      console.error("Failed to update status", err)
      alert("Failed to update status")
    }
  }

  const handleAddComment = async () => {
    if (!newComment.trim()) return
    setAddingComment(true)
    try {
      await incidentsApi.addComment(id, newComment)
      setNewComment("")
      await fetchWorkspaceData()
    } catch (err) {
      console.error("Failed to add comment", err)
      alert("Failed to add comment")
    } finally {
      setAddingComment(false)
    }
  }

  const handleTogglePin = async (entry: TimelineEntry) => {
    const isPinned = pinnedEvidence.some(p => p.evidence_id === (entry.security_event_id || entry.alert_id || entry.correlation_id))
    
    let evType = ""
    let evId = ""
    if (entry.entry_type === "SECURITY_EVENT") { evType = "SECURITY_EVENT"; evId = entry.security_event_id! }
    else if (entry.entry_type === "ALERT") { evType = "ALERT"; evId = entry.alert_id! }
    else if (entry.entry_type === "CORRELATION") { evType = "CORRELATION"; evId = entry.correlation_id! }
    else return

    try {
      if (isPinned) {
        await incidentsApi.removeEvidence(id, evType, evId)
        setPinnedEvidence(prev => prev.filter(p => p.evidence_id !== evId))
      } else {
        await incidentsApi.addEvidence(id, { evidence_type: evType as any, evidence_id: evId })
        setPinnedEvidence(prev => [...prev, { evidence_type: evType, evidence_id: evId }])
      }
      fetchWorkspaceData()
    } catch (e) {
      console.error(e)
    }
  }

  const handleEntityClick = (type: string, value: string) => {
    setSearchQuery(value)
  }

  const scrollToTimelineItem = (itemId: string) => {
    const el = document.getElementById(`timeline-item-${itemId}`)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      el.classList.add('bg-zinc-900', 'transition-colors', 'duration-1000')
      setTimeout(() => el.classList.remove('bg-zinc-900'), 2000)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[50vh]">
        <Loader2 className="h-8 w-8 animate-spin text-zinc-500" />
      </div>
    )
  }

  if (!incident) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-white mb-2">Incident Not Found</h2>
        <Button onClick={() => router.push("/incidents")} variant="outline">Back to Incidents</Button>
      </div>
    )
  }

  // Calculate Metrics
  const eventCount = timeline.filter(t => t.entry_type === "SECURITY_EVENT").length
  const alertCount = timeline.filter(t => t.entry_type === "ALERT").length
  const correlationCount = timeline.filter(t => t.entry_type === "CORRELATION").length
  const ipCount = entities?.source_ips.length || 0
  const userCount = entities?.users.length || 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push("/incidents")} className="hover:bg-zinc-800">
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-white tracking-tight">{incident.incident_number}</h1>
                <SeverityBadge severity={incident.severity} className="text-sm px-3 py-1" />
              {incident.risk_score && (
                <Badge variant="outline" className="border-orange-500 text-orange-500">Risk {incident.risk_score}</Badge>
              )}
            </div>
            <p className="text-zinc-400 text-sm mt-1">{incident.title}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <Select value={incident.status} onValueChange={handleStatusChange}>
            <SelectTrigger className="w-[180px] bg-zinc-900 border-zinc-800 text-white">
              <SelectValue placeholder="Change Status" />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-800 text-white">
              <SelectItem value="OPEN">Open</SelectItem>
              <SelectItem value="INVESTIGATING">Investigating</SelectItem>
              <SelectItem value="CONTAINED">Contained</SelectItem>
              <SelectItem value="RESOLVED">Resolved</SelectItem>
              <SelectItem value="CLOSED">Closed</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid gap-6 grid-cols-1 lg:grid-cols-4">
        
        {/* Left/Main Column - Workspace */}
        <div className="lg:col-span-3 space-y-6">
          
          {/* Investigation Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
            <div className="bg-zinc-900 border border-zinc-800 rounded p-3 text-center">
              <div className="text-xl font-bold text-white">{eventCount}</div>
              <div className="text-xs text-zinc-500 uppercase">Events</div>
            </div>
            <div className="bg-zinc-900 border border-zinc-800 rounded p-3 text-center">
              <div className="text-xl font-bold text-white">{alertCount}</div>
              <div className="text-xs text-zinc-500 uppercase">Alerts</div>
            </div>
            <div className="bg-zinc-900 border border-zinc-800 rounded p-3 text-center">
              <div className="text-xl font-bold text-white">{correlationCount}</div>
              <div className="text-xs text-zinc-500 uppercase">Correlations</div>
            </div>
            <div className="bg-zinc-900 border border-zinc-800 rounded p-3 text-center">
              <div className="text-xl font-bold text-white">{pinnedEvidence.length}</div>
              <div className="text-xs text-zinc-500 uppercase">Key Evidence</div>
            </div>
            <div className="bg-zinc-900 border border-zinc-800 rounded p-3 text-center">
              <div className="text-xl font-bold text-white">{ipCount}</div>
              <div className="text-xs text-zinc-500 uppercase">Source IPs</div>
            </div>
            <div className="bg-zinc-900 border border-zinc-800 rounded p-3 text-center">
              <div className="text-xl font-bold text-white">{userCount}</div>
              <div className="text-xs text-zinc-500 uppercase">Users</div>
            </div>
          </div>

          {/* Investigation Summary Auto-Generated */}
          {incident.correlation_id && (
            <Card className="bg-blue-950/20 border-blue-900/50">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold text-blue-400 flex items-center gap-2">
                  <FileText className="h-4 w-4" /> Investigation Summary & Attack Chain
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-zinc-300 mb-4">
                  A high-confidence attack sequence was detected. Multiple security events triggered a correlation rule resulting in an escalated incident. 
                  Review the attack chain and timeline below to verify the threat and initiate containment actions.
                </p>
                {/* Visual Attack Chain */}
                <div className="flex flex-wrap items-center gap-2 bg-zinc-950 p-3 rounded-md border border-zinc-800">
                  <div className="flex items-center gap-2 text-xs font-medium bg-zinc-900 px-2 py-1 rounded text-zinc-300">
                    <Activity className="h-3 w-3" /> Brute Force
                  </div>
                  <ArrowRight className="h-3 w-3 text-zinc-600" />
                  <div className="flex items-center gap-2 text-xs font-medium bg-zinc-900 px-2 py-1 rounded text-zinc-300">
                    <Activity className="h-3 w-3" /> Successful Login
                  </div>
                  <ArrowRight className="h-3 w-3 text-zinc-600" />
                  <div className="flex items-center gap-2 text-xs font-medium bg-zinc-900 px-2 py-1 rounded text-zinc-300">
                    <Activity className="h-3 w-3" /> Admin Login
                  </div>
                  <ArrowRight className="h-3 w-3 text-zinc-600" />
                  <div className="flex items-center gap-2 text-xs font-medium bg-zinc-900 px-2 py-1 rounded text-zinc-300">
                    <Activity className="h-3 w-3" /> Admin Action
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          <Tabs defaultValue="timeline" className="w-full">
            <TabsList className="bg-zinc-900 border border-zinc-800 p-1">
              <TabsTrigger value="timeline" className="data-[state=active]:bg-zinc-800 text-zinc-400 data-[state=active]:text-white">Investigation Timeline</TabsTrigger>
              <TabsTrigger value="notes" className="data-[state=active]:bg-zinc-800 text-zinc-400 data-[state=active]:text-white">Analyst Notes</TabsTrigger>
              <TabsTrigger value="response" className="data-[state=active]:bg-zinc-800 text-zinc-400 data-[state=active]:text-white">Response</TabsTrigger>
            </TabsList>
            
            <TabsContent value="timeline" className="mt-6 space-y-4">
              <div className="flex items-center gap-4 mb-6">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
                  <input 
                    type="text" 
                    placeholder="Search timeline..." 
                    className="w-full bg-zinc-900 border border-zinc-800 rounded-md py-2 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-zinc-700"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
                <Select value={filterTypes} onValueChange={(val) => setFilterTypes(val || '')}>
                  <SelectTrigger className="w-[180px] bg-zinc-900 border-zinc-800 text-white">
                    <SelectValue placeholder="All Events" />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-900 border-zinc-800 text-white">
                    <SelectItem value="">All Events</SelectItem>
                    <SelectItem value="SECURITY_EVENT">Security Events</SelectItem>
                    <SelectItem value="ALERT">Alerts</SelectItem>
                    <SelectItem value="CORRELATION">Correlations</SelectItem>
                    <SelectItem value="COMMENT">Notes</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-0">
                {timeline.length === 0 ? (
                  <p className="text-zinc-500 text-center py-12">No timeline events found.</p>
                ) : (
                  timeline.map(entry => (
                    <div id={`timeline-item-${entry.id}`} key={entry.id}>
                      <TimelineEntryComponent 
                        entry={entry} 
                        isPinned={pinnedEvidence.some(p => p.evidence_id === (entry.security_event_id || entry.alert_id || entry.correlation_id))}
                        onTogglePin={handleTogglePin}
                        onEventClick={setSelectedEvent}
                      />
                    </div>
                  ))
                )}
              </div>
            </TabsContent>

            <TabsContent value="notes" className="mt-6">
              <Card className="bg-zinc-900 border-zinc-800">
                <CardContent className="pt-6 space-y-4">
                  <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
                    {timeline.filter(t => t.entry_type === 'COMMENT').length === 0 ? (
                      <p className="text-zinc-500 text-sm italic">No notes yet. Add one below.</p>
                    ) : (
                      timeline.filter(t => t.entry_type === 'COMMENT').map(c => (
                        <div key={c.id} className="bg-zinc-950 p-3 rounded-md border border-zinc-800">
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-xs font-semibold text-blue-400">{c.title}</span>
                            <span className="text-xs text-zinc-500">{format(new Date(c.occurred_at), 'MMM d, HH:mm')}</span>
                          </div>
                          <p className="text-sm text-zinc-300 whitespace-pre-wrap">{c.description}</p>
                        </div>
                      ))
                    )}
                  </div>
                  
                  <div className="pt-4 border-t border-zinc-800">
                    <Textarea 
                      placeholder="Add a new investigation note..."
                      value={newComment}
                      onChange={(e) => setNewComment(e.target.value)}
                      className="bg-zinc-950 border-zinc-800 text-white min-h-[100px] mb-2"
                    />
                    <Button 
                      onClick={handleAddComment} 
                      disabled={!newComment.trim() || addingComment}
                      className="w-full bg-blue-600 hover:bg-blue-700"
                    >
                      {addingComment ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
                      Save Note
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="response" className="mt-6">
              <ResponseActionsPanel incidentId={id} applicationId={incident.application_id} />
            </TabsContent>
          </Tabs>
        </div>

        {/* Right Sidebar - Entities & Evidence */}
        <div className="space-y-6">
          <KeyEvidencePanel 
            timeline={timeline}
            pinnedEvidence={pinnedEvidence}
            onItemClick={scrollToTimelineItem}
          />

          <EntitySummary 
            entities={entities} 
            onEntityClick={handleEntityClick} 
          />

          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm">Metadata</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-zinc-500" />
                <span className="text-zinc-400">Detected: {format(new Date(incident.detected_at), 'MMM d, HH:mm')}</span>
              </div>
              {incident.contained_at && (
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-emerald-500" />
                  <span className="text-zinc-400">Contained: {format(new Date(incident.contained_at), 'MMM d, HH:mm')}</span>
                </div>
              )}
              {incident.resolved_at && (
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-blue-500" />
                  <span className="text-zinc-400">Resolved: {format(new Date(incident.resolved_at), 'MMM d, HH:mm')}</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Event Details Dialog */}
      <Dialog open={!!selectedEvent} onOpenChange={(open) => !open && setSelectedEvent(null)}>
        <DialogContent className="bg-zinc-900 border-zinc-800 text-white max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-emerald-500" />
              Event Details
            </DialogTitle>
            <DialogDescription>Detailed view of the selected timeline event.</DialogDescription>
          </DialogHeader>
          
          {selectedEvent && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-zinc-500 block mb-1">Timestamp</span>
                  <span>{format(new Date(selectedEvent.occurred_at), "yyyy-MM-dd HH:mm:ss")}</span>
                </div>
                <div>
                  <span className="text-zinc-500 block mb-1">Type</span>
                  <span>{selectedEvent.title}</span>
                </div>
                <div>
                  <span className="text-zinc-500 block mb-1">Source IP</span>
                  <span>{selectedEvent.source_ip || "N/A"}</span>
                </div>
                <div>
                  <span className="text-zinc-500 block mb-1">Username</span>
                  <span>{selectedEvent.username || "N/A"}</span>
                </div>
                <div className="col-span-2">
                  <span className="text-zinc-500 block mb-1">Description</span>
                  <span className="break-all">{selectedEvent.description || "N/A"}</span>
                </div>
              </div>
              
              <div className="pt-4 border-t border-zinc-800">
                <h4 className="text-sm font-semibold mb-2">Raw Metadata</h4>
                <div className="bg-zinc-950 p-3 rounded-md border border-zinc-800 overflow-x-auto">
                  <pre className="text-xs text-zinc-300">
                    {JSON.stringify(selectedEvent.metadata_fields || {}, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
