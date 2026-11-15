import { useState, useEffect } from "react"
import { ShieldAlert, Play, CheckCircle2, XCircle, Clock, Search, StopCircle, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { 
  getResponseActions, createResponseAction, approveResponseAction, 
  rejectResponseAction, cancelResponseAction, executeResponseAction,
  getApplicationCapabilities
} from "@/lib/api/response"
import { ResponseAction, ApplicationResponseCapability } from "@/lib/types/response"

export function ResponseActionsPanel({ incidentId, applicationId }: { incidentId: string, applicationId: string }) {
  const [actions, setActions] = useState<ResponseAction[]>([])
  const [capabilities, setCapabilities] = useState<ApplicationResponseCapability[]>([])
  const [loading, setLoading] = useState(true)
  
  // Request Modal
  const [isRequestModalOpen, setIsRequestModalOpen] = useState(false)
  const [requestActionType, setRequestActionType] = useState("")
  const [requestTargetType, setRequestTargetType] = useState("")
  const [requestTargetValue, setRequestTargetValue] = useState("")
  
  // Reject Modal
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false)
  const [rejectingId, setRejectingId] = useState("")
  const [rejectReason, setRejectReason] = useState("")

  const fetchData = async () => {
    setLoading(true)
    try {
      const [actionsData, capsData] = await Promise.all([
        getResponseActions({ incident_id: incidentId, page_size: 50 }),
        getApplicationCapabilities(applicationId)
      ])
      setActions(actionsData.items || [])
      setCapabilities(capsData || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [incidentId, applicationId])

  const handleRequest = async () => {
    try {
      await createResponseAction({
        incident_id: incidentId,
        application_id: applicationId,
        action_type: requestActionType,
        target_type: requestTargetType,
        target_value: requestTargetValue
      })
      setIsRequestModalOpen(false)
      setRequestTargetValue("")
      fetchData()
    } catch (e) {
      console.error(e)
    }
  }

  const handleApprove = async (id: string) => {
    try {
      await approveResponseAction(id)
      fetchData()
    } catch (e) { console.error(e) }
  }

  const handleExecute = async (id: string) => {
    try {
      await executeResponseAction(id)
      fetchData()
    } catch (e) { console.error(e) }
  }

  const handleCancel = async (id: string) => {
    try {
      await cancelResponseAction(id)
      fetchData()
    } catch (e) { console.error(e) }
  }

  const handleReject = async () => {
    try {
      await rejectResponseAction(rejectingId, rejectReason)
      setIsRejectModalOpen(false)
      setRejectReason("")
      fetchData()
    } catch (e) { console.error(e) }
  }

  const getStatusBadge = (status: string) => {
    switch(status) {
      case "PENDING_APPROVAL": return <Badge variant="warning">Pending</Badge>
      case "APPROVED": return <Badge className="bg-blue-600 hover:bg-blue-700">Approved</Badge>
      case "EXECUTING": return <Badge variant="outline" className="animate-pulse">Executing...</Badge>
      case "SUCCEEDED": return <Badge variant="default" className="bg-emerald-600 hover:bg-emerald-700">Succeeded</Badge>
      case "FAILED": return <Badge variant="destructive">Failed</Badge>
      case "REJECTED": return <Badge variant="destructive">Rejected</Badge>
      case "CANCELLED": return <Badge variant="secondary">Cancelled</Badge>
      default: return <Badge variant="outline">{status}</Badge>
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Security Response Actions</h3>
        <Button onClick={() => setIsRequestModalOpen(true)} size="sm" className="bg-red-600 hover:bg-red-700">
          <ShieldAlert className="h-4 w-4 mr-2" /> Request Action
        </Button>
      </div>

      <div className="space-y-3">
        {actions.length === 0 ? (
          <div className="text-center p-8 border border-dashed border-zinc-800 rounded-md text-zinc-500">
            No response actions requested yet.
          </div>
        ) : (
          actions.map(action => (
            <Card key={action.id} className="bg-zinc-900 border-zinc-800">
              <CardContent className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold text-zinc-200">{action.action_type}</span>
                    {getStatusBadge(action.status)}
                  </div>
                  <div className="text-sm text-zinc-400 mt-1">
                    Target: <Badge variant="outline" className="mr-1">{action.target_type}</Badge> 
                    <span className="font-mono text-zinc-300">{action.target_value}</span>
                  </div>
                  {action.result_summary && (
                    <div className="text-sm text-zinc-500 mt-2 bg-zinc-950 p-2 rounded">
                      Result: {action.result_summary}
                    </div>
                  )}
                </div>
                
                <div className="flex items-center gap-2">
                  {action.status === "PENDING_APPROVAL" && (
                    <>
                      <Button size="sm" variant="outline" className="border-green-800 text-green-500 hover:bg-green-900/30" onClick={() => handleApprove(action.id)}>
                        <CheckCircle2 className="h-4 w-4 mr-1" /> Approve
                      </Button>
                      <Button size="sm" variant="outline" className="border-red-800 text-red-500 hover:bg-red-900/30" onClick={() => { setRejectingId(action.id); setIsRejectModalOpen(true); }}>
                        <XCircle className="h-4 w-4 mr-1" /> Reject
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => handleCancel(action.id)}>Cancel</Button>
                    </>
                  )}
                  {action.status === "APPROVED" && (
                    <>
                      <Button size="sm" className="bg-blue-600 hover:bg-blue-700" onClick={() => handleExecute(action.id)}>
                        <Play className="h-4 w-4 mr-1" /> Execute
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => handleCancel(action.id)}>Cancel</Button>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      <Dialog open={isRequestModalOpen} onOpenChange={setIsRequestModalOpen}>
        <DialogContent className="bg-zinc-950 border-zinc-800 text-white">
          <DialogHeader>
            <DialogTitle>Request Security Action</DialogTitle>
            <DialogDescription>
              This action will require administrative approval before executing on the target application.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Action Type</label>
              <Select value={requestActionType} onValueChange={(val) => setRequestActionType(val || '')}>
                <SelectTrigger className="bg-zinc-900 border-zinc-800">
                  <SelectValue placeholder="Select action..." />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-zinc-800 text-white">
                  {capabilities.map(cap => (
                    <SelectItem key={cap.id} value={cap.action_type}>{cap.action_type}</SelectItem>
                  ))}
                  {capabilities.length === 0 && <SelectItem value="none" disabled>No capabilities configured for this app</SelectItem>}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Target Type</label>
              <Select value={requestTargetType} onValueChange={(val) => setRequestTargetType(val || '')}>
                <SelectTrigger className="bg-zinc-900 border-zinc-800">
                  <SelectValue placeholder="Select target type..." />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-zinc-800 text-white">
                  <SelectItem value="IP_ADDRESS">IP_ADDRESS</SelectItem>
                  <SelectItem value="USER_ID">USER_ID</SelectItem>
                  <SelectItem value="USERNAME">USERNAME</SelectItem>
                  <SelectItem value="SESSION_ID">SESSION_ID</SelectItem>
                  <SelectItem value="API_KEY_ID">API_KEY_ID</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Target Value</label>
              <Input 
                value={requestTargetValue} 
                onChange={(e) => setRequestTargetValue(e.target.value)} 
                className="bg-zinc-900 border-zinc-800"
                placeholder="e.g. 192.168.1.10"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setIsRequestModalOpen(false)}>Cancel</Button>
            <Button onClick={handleRequest} disabled={!requestActionType || !requestTargetType || !requestTargetValue}>Request Approval</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      <Dialog open={isRejectModalOpen} onOpenChange={setIsRejectModalOpen}>
        <DialogContent className="bg-zinc-950 border-zinc-800 text-white">
          <DialogHeader>
            <DialogTitle>Reject Action</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Reason for Rejection</label>
              <Input 
                value={rejectReason} 
                onChange={(e) => setRejectReason(e.target.value)} 
                className="bg-zinc-900 border-zinc-800"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setIsRejectModalOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleReject} disabled={!rejectReason}>Confirm Rejection</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
