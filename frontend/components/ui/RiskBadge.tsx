import { cn } from "@/lib/utils"

export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL' | string

interface RiskBadgeProps {
  level?: RiskLevel
  score?: number
  className?: string
}

export function getRiskLevel(score: number): RiskLevel {
  if (score >= 75) return 'CRITICAL'
  if (score >= 50) return 'HIGH'
  if (score >= 25) return 'MODERATE'
  return 'LOW'
}

export function RiskBadge({ level, score, className }: RiskBadgeProps) {
  const finalLevel = level ? level : (score !== undefined ? getRiskLevel(score) : 'LOW')
  const upperLevel = finalLevel?.toUpperCase() || 'LOW'
  
  const getStyles = (lvl: string) => {
    switch (lvl) {
      case 'CRITICAL':
        return 'bg-purple-500/10 text-purple-500 border-purple-500/20'
      case 'HIGH':
        return 'bg-red-500/10 text-red-500 border-red-500/20'
      case 'MODERATE':
        return 'bg-orange-500/10 text-orange-500 border-orange-500/20'
      case 'LOW':
      default:
        return 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'
    }
  }

  return (
    <span className={cn("inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider", getStyles(upperLevel), className)}>
      {upperLevel} {score !== undefined ? `(${score})` : ''}
    </span>
  )
}
