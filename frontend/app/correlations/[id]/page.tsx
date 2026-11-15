"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { PageHeader } from "@/components/layout/PageHeader"
import { correlationsApi } from "@/lib/api/correlations"
import { Correlation } from "@/lib/types/correlation"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { format } from "date-fns"

export default function CorrelationDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter()
  const [correlation, setCorrelation] = useState<Correlation | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    correlationsApi.getCorrelation(params.id)
      .then(res => setCorrelation(res))
      .finally(() => setLoading(false))
  }, [params.id])

  const handleCreateIncident = async () => {
    setLoading(true)
    try {
      const res = await correlationsApi.createIncident(params.id)
      try {
        router.push(`/incidents/${res.incident_id}`)
      } catch (navErr) {
        window.location.href = `/incidents/${res.incident_id}`
      }
    } catch (err) {
      console.error(err)
      alert(`Failed to create incident: ${err instanceof Error ? err.message : String(err)}`)
      setLoading(false)
    }
  }

  if (loading) return <div className="p-8 text-zinc-500">Loading correlation details...</div>
  if (!correlation) return <div className="p-8 text-red-500">Correlation not found.</div>

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <PageHeader 
          title={correlation.name}
          description={`Correlated sequence spanning ${format(new Date(correlation.first_event_at), 'MMM d, HH:mm:ss')} to ${format(new Date(correlation.last_event_at), 'HH:mm:ss')}`}
        />
        <Button
          variant="default"
          onClick={handleCreateIncident}
          className="bg-blue-600 hover:bg-blue-700"
        >
          Create Incident
        </Button>
      </div>
      
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <CardTitle>Attack Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              {correlation.evidence && correlation.evidence.length > 0 ? (
                <div className="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-zinc-700 before:to-transparent">
                  {correlation.evidence.map((ev, i) => (
                    <div key={ev.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                      <div className="flex items-center justify-center w-10 h-10 rounded-full border border-zinc-700 bg-zinc-900 text-zinc-400 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                        {i + 1}
                      </div>
                      <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded border border-zinc-800 bg-zinc-900/50 hover:bg-zinc-800/50 transition-colors">
                        <div className="flex items-center justify-between mb-1">
                          <Badge variant="outline">{ev.type}</Badge>
                          <time className="font-mono text-xs text-zinc-500">{format(new Date(ev.timestamp), 'HH:mm:ss')}</time>
                        </div>
                        <div className="font-medium text-sm text-zinc-300">
                          {ev.type === 'EVENT' ? ev.data.event_type : ev.data.title}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-zinc-500">Timeline not available.</p>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="bg-zinc-900 border-zinc-800">
            <CardHeader>
              <CardTitle>Risk & Priority</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <span className="text-zinc-500 text-sm">Severity</span>
                <p className="mt-1">
                  <Badge variant={
                    correlation.severity === 'CRITICAL' ? 'destructive' :
                    correlation.severity === 'HIGH' ? 'destructive' :
                    correlation.severity === 'MEDIUM' ? 'warning' : 'secondary'
                  }>{correlation.severity}</Badge>
                </p>
              </div>
              
              <div className="pt-4 border-t border-zinc-800">
                <span className="text-zinc-500 text-sm">Risk Score</span>
                <div className="flex items-center gap-3 mt-1">
                  <span className="text-3xl font-bold">{correlation.risk_score || 0}</span>
                  <span className="text-zinc-500">/ 100</span>
                  {correlation.risk_level && (
                    <Badge variant={
                      correlation.risk_level === 'CRITICAL' ? 'destructive' :
                      correlation.risk_level === 'HIGH' ? 'destructive' :
                      correlation.risk_level === 'MODERATE' ? 'warning' : 'secondary'
                    }>{correlation.risk_level}</Badge>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {correlation.risk_factors && (
            <Card className="bg-zinc-900 border-zinc-800">
              <CardHeader>
                <CardTitle className="text-sm font-medium text-zinc-400 uppercase tracking-wider">
                  Risk Factors
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(correlation.risk_factors).map(([factor, score]) => (
                    <div key={factor} className="flex items-center justify-between">
                      <span className="text-zinc-300 capitalize">{factor.replace('_', ' ')}</span>
                      <span className="font-mono text-zinc-400">+{score}</span>
                    </div>
                  ))}
                  <div className="pt-3 mt-3 border-t border-zinc-800 flex items-center justify-between font-medium">
                    <span>Final Risk Score</span>
                    <span>{correlation.risk_score}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {correlation.generated_alert_id && (
            <Card className="bg-blue-950/20 border-blue-900/50">
              <CardHeader>
                <CardTitle className="text-blue-400">SOC Alert</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-blue-200/70 mb-4">
                  This correlation sequence has been escalated to the analyst queue.
                </p>
                <Link href={`/alerts/${correlation.generated_alert_id}`} className="inline-flex shrink-0 items-center justify-center rounded-lg border bg-background text-sm font-medium w-full h-8 px-2.5 border-blue-900/50 text-blue-400 hover:bg-blue-900/30">
                  View Generated Alert
                </Link>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
