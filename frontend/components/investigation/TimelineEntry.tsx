import { format } from "date-fns"
import { Shield, AlertTriangle, MessageSquare, Activity, ActivityIcon, Link as LinkIcon, Star, ArrowRight } from "lucide-react"
import { TimelineEntry as TimelineEntryType } from "@/lib/types/investigation"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import Link from "next/link"

interface Props {
  entry: TimelineEntryType
  isPinned: boolean
  onTogglePin: (entry: TimelineEntryType) => void
  onEventClick?: (entry: TimelineEntryType) => void
}

export function TimelineEntry({ entry, isPinned, onTogglePin, onEventClick }: Props) {
  const getIcon = () => {
    switch (entry.entry_type) {
      case "ALERT": return <AlertTriangle className="h-5 w-5 text-red-500" />
      case "CORRELATION": return <Shield className="h-5 w-5 text-purple-500" />
      case "COMMENT": return <MessageSquare className="h-5 w-5 text-blue-500" />
      case "INCIDENT_ACTIVITY": return <Activity className="h-5 w-5 text-zinc-500" />
      default: return <ActivityIcon className="h-5 w-5 text-emerald-500" />
    }
  }

  const getBorderColor = () => {
    switch (entry.entry_type) {
      case "ALERT": return "border-red-900/50 hover:border-red-700/50"
      case "CORRELATION": return "border-purple-900/50 hover:border-purple-700/50"
      case "COMMENT": return "border-blue-900/50"
      case "INCIDENT_ACTIVITY": return "border-zinc-800"
      default: return "border-emerald-900/50 hover:border-emerald-700/50"
    }
  }
  
  const getSeverityBadge = () => {
    if (!entry.severity) return null
    return (
      <Badge variant={entry.severity === 'CRITICAL' || entry.severity === 'HIGH' ? 'destructive' : 'secondary'} className="text-[10px] h-5">
        {entry.severity}
      </Badge>
    )
  }

  const canPin = ["SECURITY_EVENT", "ALERT", "CORRELATION"].includes(entry.entry_type)
  const isEvent = entry.entry_type === "SECURITY_EVENT"

  return (
    <div className="relative pl-8 pb-8 group">
      <div className="absolute left-3.5 top-8 bottom-0 w-0.5 bg-zinc-800" />
      
      <div className="absolute left-0 top-1 h-7 w-7 rounded-full bg-zinc-950 border border-zinc-800 flex items-center justify-center z-10">
        {getIcon()}
      </div>

      <div 
        className={`bg-zinc-950 rounded-lg p-4 border ${getBorderColor()} shadow-sm transition-colors ${isEvent ? 'cursor-pointer' : ''}`}
        onClick={() => {
          if (isEvent && onEventClick) onEventClick(entry)
        }}
      >
        <div className="flex justify-between items-start mb-2">
          <div className="flex items-center gap-2">
            <span className="font-medium text-white">{entry.title}</span>
            {getSeverityBadge()}
            {entry.risk_score && (
              <Badge variant="outline" className="text-[10px] h-5 border-orange-500/50 text-orange-500">
                Risk {entry.risk_score}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-zinc-500 font-mono">
              {format(new Date(entry.occurred_at), "HH:mm:ss")}
            </span>
            {canPin && (
              <Button 
                variant="ghost" 
                size="icon" 
                className={`h-6 w-6 ${isPinned ? "text-yellow-500 hover:text-yellow-600" : "text-zinc-600 hover:text-zinc-400 opacity-0 group-hover:opacity-100"}`}
                onClick={(e) => { e.stopPropagation(); onTogglePin(entry); }}
                title={isPinned ? "Unpin Evidence" : "Pin Evidence"}
              >
                <Star className={`h-4 w-4 ${isPinned ? "fill-current" : ""}`} />
              </Button>
            )}
          </div>
        </div>

        {entry.description && (
          <p className="text-sm text-zinc-400 mb-3 whitespace-pre-wrap">{entry.description}</p>
        )}

        {/* Action Links for Alert and Correlation */}
        {entry.entry_type === "ALERT" && entry.alert_id && (
          <Link href={`/alerts/${entry.alert_id}`} className="text-xs text-blue-400 hover:underline flex items-center gap-1 mb-3">
            View Alert <ArrowRight className="h-3 w-3" />
          </Link>
        )}
        {entry.entry_type === "CORRELATION" && entry.correlation_id && (
          <Link href={`/correlations/${entry.correlation_id}`} className="text-xs text-blue-400 hover:underline flex items-center gap-1 mb-3">
            View Correlation <ArrowRight className="h-3 w-3" />
          </Link>
        )}

        {(entry.source_ip || entry.username || entry.metadata_fields?.app_id || entry.metadata_fields?.request_path) && (
          <div className="flex flex-wrap gap-2 mt-2">
            {entry.source_ip && (
              <div className="text-xs bg-zinc-900 border border-zinc-800 px-2 py-1 rounded text-zinc-300">
                IP: {entry.source_ip}
              </div>
            )}
            {entry.username && (
              <div className="text-xs bg-zinc-900 border border-zinc-800 px-2 py-1 rounded text-zinc-300">
                User: {entry.username}
              </div>
            )}
            {entry.metadata_fields?.request_path && (
              <div className="text-xs bg-zinc-900 border border-zinc-800 px-2 py-1 rounded text-zinc-300 max-w-[200px] truncate" title={entry.metadata_fields.request_path}>
                Path: {entry.metadata_fields.request_path}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
