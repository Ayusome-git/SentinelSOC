"use client";

import { useState, useEffect } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { getResponseActions, approveResponseAction, executeResponseAction, rejectResponseAction, cancelResponseAction } from "@/lib/api/response";
import { ResponseAction } from "@/lib/types/response";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2, Play, CheckCircle2, XCircle, ShieldAlert } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { format } from "date-fns";

export default function ResponseActionsPage() {
  const [actions, setActions] = useState<ResponseAction[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [rejectingId, setRejectingId] = useState("");
  const [rejectReason, setRejectReason] = useState("");
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false);

  const fetchActions = async () => {
    setLoading(true);
    try {
      const data = await getResponseActions({ page_size: 100 });
      setActions(data.items || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActions();
  }, []);

  const handleApprove = async (id: string) => {
    await approveResponseAction(id);
    fetchActions();
  };

  const handleExecute = async (id: string) => {
    await executeResponseAction(id);
    fetchActions();
  };

  const handleCancel = async (id: string) => {
    await cancelResponseAction(id);
    fetchActions();
  };

  const handleReject = async () => {
    await rejectResponseAction(rejectingId, rejectReason);
    setIsRejectModalOpen(false);
    setRejectReason("");
    fetchActions();
  };

  const getStatusBadge = (status: string) => {
    switch(status) {
      case "PENDING_APPROVAL": return <Badge variant="warning">Pending</Badge>;
      case "APPROVED": return <Badge className="bg-blue-600">Approved</Badge>;
      case "EXECUTING": return <Badge variant="outline" className="animate-pulse">Executing...</Badge>;
      case "SUCCEEDED": return <Badge variant="default" className="bg-emerald-600 hover:bg-emerald-700">Succeeded</Badge>;
      case "FAILED": return <Badge variant="destructive">Failed</Badge>;
      case "REJECTED": return <Badge variant="destructive">Rejected</Badge>;
      case "CANCELLED": return <Badge variant="secondary">Cancelled</Badge>;
      default: return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Security Response Actions" 
        description="Monitor and approve automated and manual security actions across connected applications."
      />
      
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
        {loading ? (
          <div className="flex justify-center p-8"><Loader2 className="h-6 w-6 animate-spin text-zinc-500" /></div>
        ) : (
          <Table>
            <TableHeader className="bg-zinc-950/50">
              <TableRow className="border-zinc-800 hover:bg-transparent">
                <TableHead className="text-zinc-400">Action</TableHead>
                <TableHead className="text-zinc-400">Target</TableHead>
                <TableHead className="text-zinc-400">Status</TableHead>
                <TableHead className="text-zinc-400">Requested At</TableHead>
                <TableHead className="text-zinc-400 text-right">Operations</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {actions.length === 0 ? (
                <TableRow className="border-zinc-800 hover:bg-zinc-900/50 transition-colors">
                  <TableCell colSpan={5} className="text-center text-zinc-500 py-8">
                    No response actions found
                  </TableCell>
                </TableRow>
              ) : (
                actions.map((action) => (
                  <TableRow key={action.id} className="border-zinc-800 hover:bg-zinc-900/50 transition-colors">
                    <TableCell>
                      <div className="font-medium text-zinc-200">{action.action_type}</div>
                      <div className="text-xs text-zinc-500">App: {action.application_id.substring(0,8)}...</div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Badge variant="outline" className="text-[10px] py-0">{action.target_type}</Badge>
                        <span className="font-mono text-sm text-zinc-300">{action.target_value}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {getStatusBadge(action.status)}
                    </TableCell>
                    <TableCell className="text-zinc-400 text-sm">
                      {format(new Date(action.requested_at), "MMM d, HH:mm:ss")}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        {action.status === "PENDING_APPROVAL" && (
                          <>
                            <Button size="sm" variant="outline" className="border-green-800 text-green-500 hover:bg-green-900/30 h-8" onClick={() => handleApprove(action.id)}>
                              <CheckCircle2 className="h-3 w-3 mr-1" /> Approve
                            </Button>
                            <Button size="sm" variant="outline" className="border-red-800 text-red-500 hover:bg-red-900/30 h-8" onClick={() => { setRejectingId(action.id); setIsRejectModalOpen(true); }}>
                              <XCircle className="h-3 w-3 mr-1" /> Reject
                            </Button>
                          </>
                        )}
                        {action.status === "APPROVED" && (
                          <>
                            <Button size="sm" className="bg-blue-600 hover:bg-blue-700 h-8" onClick={() => handleExecute(action.id)}>
                              <Play className="h-3 w-3 mr-1" /> Execute
                            </Button>
                            <Button size="sm" variant="ghost" className="h-8" onClick={() => handleCancel(action.id)}>Cancel</Button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        )}
      </div>

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
  );
}
