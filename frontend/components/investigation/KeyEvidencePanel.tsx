import { Star, Shield, AlertTriangle, ActivityIcon } from "lucide-react"
import { TimelineEntry } from "@/lib/types/investigation"

interface Props {
  timeline: TimelineEntry[]
  pinnedEvidence: any[]
  onItemClick: (id: string) => void
}

export function KeyEvidencePanel({ timeline, pinnedEvidence, onItemClick }: Props) {
  if (pinnedEvidence.length === 0) return null

  // Map pinned evidence back to timeline entries to display their info
  const pinnedEntries = pinnedEvidence.map(pe => {
    return timeline.find(te => 
      (te.entry_type === "SECURITY_EVENT" && te.security_event_id === pe.evidence_id) ||
      (te.entry_type === "ALERT" && te.alert_id === pe.evidence_id) ||
      (te.entry_type === "CORRELATION" && te.correlation_id === pe.evidence_id)
    )
  }).filter(Boolean) as TimelineEntry[]

  const getIcon = (type: string) => {
    switch (type) {
      case "ALERT": return <AlertTriangle className="h-3 w-3 text-red-500" />
      case "CORRELATION": return <Shield className="h-3 w-3 text-purple-500" />
      default: return <ActivityIcon className="h-3 w-3 text-emerald-500" />
    }
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 mb-6">
      <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
        <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" /> 
        Key Evidence
      </h3>
      <div className="space-y-2">
        {pinnedEntries.map(entry => (
          <div 
            key={entry.id}
            onClick={() => onItemClick(entry.id)}
            className="flex items-start gap-2 p-2 bg-zinc-950 border border-zinc-800 rounded cursor-pointer hover:border-zinc-700 transition-colors"
          >
            <div className="mt-1">{getIcon(entry.entry_type)}</div>
            <div className="overflow-hidden">
              <p className="text-sm text-zinc-300 truncate font-medium">{entry.title}</p>
              <p className="text-xs text-zinc-500 truncate">{entry.description || "No description"}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
