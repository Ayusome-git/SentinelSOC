import { cn } from "@/lib/utils"

export type Severity = 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string

interface SeverityBadgeProps {
  severity: Severity
  className?: string
}

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  const upperSeverity = severity?.toUpperCase() || 'INFO'
  
  const getStyles = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-red-500/10 text-red-500 border-red-500/20'
      case 'HIGH':
        return 'bg-orange-500/10 text-orange-500 border-orange-500/20'
      case 'MEDIUM':
        return 'bg-amber-500/10 text-amber-500 border-amber-500/20'
      case 'LOW':
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
      case 'INFO':
      default:
        return 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'
    }
  }

  return (
    <span className={cn("inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider", getStyles(upperSeverity), className)}>
      {upperSeverity}
    </span>
  )
}
