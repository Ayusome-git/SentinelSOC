"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { 
  LayoutDashboard, 
  Activity, 
  AlertTriangle, 
  ShieldAlert, 
  AppWindow, 
  Settings,
  Users,
  Target,
  Cpu,
  Globe,
  Zap,
  FileText
} from "lucide-react"
import { cn } from "@/lib/utils"
import { usePermissions } from "@/lib/permissions"

interface NavItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  permission?: string
}

interface NavGroup {
  label: string
  items: NavItem[]
}

const navigationGroups: NavGroup[] = [
  {
    label: "OVERVIEW",
    items: [
      { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    ]
  },
  {
    label: "MONITORING",
    items: [
      { name: "Events", href: "/events", icon: Activity },
      { name: "Alerts", href: "/alerts", icon: AlertTriangle },
      { name: "Incidents", href: "/incidents", icon: ShieldAlert },
      { name: "Correlations", href: "/correlations", icon: Activity },
    ]
  },
  {
    label: "DETECTION",
    items: [
      { name: "Rules", href: "/rules", icon: Target, permission: "RULES_READ" },
      { name: "ML Anomalies", href: "/settings/ml", icon: Cpu },
      { name: "Threat Intelligence", href: "/settings/threat-intelligence", icon: Globe, permission: "THREAT_INTEL_READ" },
    ]
  },
  {
    label: "INTEGRATIONS",
    items: [
      { name: "Applications", href: "/applications", icon: AppWindow },
    ]
  },
  {
    label: "REPORTING",
    items: [
      { name: "Reports", href: "/reports", icon: FileText },
    ]
  }
]

export function Sidebar() {
  const pathname = usePathname()
  const { hasPermission } = usePermissions()

  return (
    <div className="flex h-full w-64 flex-col bg-[#0a0a0a] border-r border-zinc-800 text-zinc-300">
      <div className="flex h-16 items-center px-6 border-b border-zinc-800">
        <ShieldAlert className="h-6 w-6 text-indigo-500 mr-2" />
        <span className="text-lg font-semibold text-white tracking-tight">SentinelSOC</span>
      </div>
      
      <div className="flex-1 overflow-y-auto py-6 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
        <nav className="flex-1 space-y-6 px-4">
          {navigationGroups.map((group) => {
            const visibleItems = group.items.filter(item => {
              if (!item.permission) return true
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              return hasPermission(item.permission as any)
            })

            if (visibleItems.length === 0) return null

            return (
              <div key={group.label} className="space-y-2">
                <h3 className="px-3 text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                  {group.label}
                </h3>
                <div className="space-y-1">
                  {visibleItems.map((item) => {
                    const isActive = pathname === item.href || pathname.startsWith(item.href + '/')
                    return (
                      <Link
                        key={item.name}
                        href={item.href}
                        className={cn(
                          "group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors",
                          isActive 
                            ? "bg-zinc-800/80 text-white" 
                            : "text-zinc-400 hover:bg-zinc-800/50 hover:text-white"
                        )}
                      >
                        <item.icon
                          className={cn(
                            "flex-shrink-0 -ml-1 mr-3 h-5 w-5",
                            isActive ? "text-indigo-400" : "text-zinc-500 group-hover:text-zinc-300"
                          )}
                          aria-hidden="true"
                        />
                        {item.name}
                      </Link>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </nav>
      </div>

      <div className="p-4 border-t border-zinc-800">
        <div className="flex items-center space-x-2 px-2 py-1.5 bg-zinc-900 rounded-md border border-zinc-800">
          <div className="h-2.5 w-2.5 rounded-full bg-emerald-500"></div>
          <span className="text-xs font-medium text-zinc-300">System Operational</span>
        </div>
      </div>
    </div>
  )
}

