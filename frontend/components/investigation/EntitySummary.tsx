import { EntitiesResponse, EntityCount } from "@/lib/types/investigation"
import { Users, Monitor, Link2, MapPin } from "lucide-react"

interface Props {
  entities: EntitiesResponse | null
  onEntityClick: (type: string, value: string) => void
}

export function EntitySummary({ entities, onEntityClick }: Props) {
  if (!entities) return null

  const renderSection = (title: string, items: EntityCount[], icon: React.ReactNode, type: string) => {
    if (items.length === 0) return null
    return (
      <div className="mb-6 last:mb-0">
        <h4 className="text-sm font-semibold text-zinc-300 flex items-center gap-2 mb-3">
          {icon} {title}
        </h4>
        <div className="space-y-2">
          {items.map(item => (
            <div 
              key={item.value} 
              className="flex justify-between items-center bg-zinc-950 border border-zinc-800 p-2 rounded hover:border-zinc-700 cursor-pointer transition-colors"
              onClick={() => onEntityClick(type, item.value)}
            >
              <span className="text-sm text-zinc-300 truncate mr-2" title={item.value}>{item.value}</span>
              <span className="text-xs bg-zinc-900 text-zinc-400 px-2 py-0.5 rounded-full border border-zinc-800">
                {item.event_count}
              </span>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 h-full">
      <h3 className="text-lg font-semibold text-white mb-4">Entities</h3>
      <div className="overflow-y-auto pr-2" style={{ maxHeight: 'calc(100vh - 300px)' }}>
        {renderSection("Source IPs", entities.source_ips, <Monitor className="h-4 w-4 text-blue-400" />, "source_ip")}
        {renderSection("Users", entities.users, <Users className="h-4 w-4 text-emerald-400" />, "username")}
        {renderSection("Request Paths", entities.request_paths, <Link2 className="h-4 w-4 text-purple-400" />, "request_path")}
        {renderSection("Sessions", entities.sessions, <MapPin className="h-4 w-4 text-orange-400" />, "session")}
        
        {(!entities.source_ips.length && !entities.users.length && !entities.request_paths.length && !entities.sessions.length) && (
          <p className="text-sm text-zinc-500 italic">No entities detected in this incident scope.</p>
        )}
      </div>
    </div>
  )
}
