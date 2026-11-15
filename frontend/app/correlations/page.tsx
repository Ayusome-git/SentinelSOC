"use client"

import { useState, useEffect } from "react"
import { PageHeader } from "@/components/layout/PageHeader"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { correlationsApi } from "@/lib/api/correlations"
import { Correlation } from "@/lib/types/correlation"
import Link from "next/link"
import { format } from "date-fns"

export default function CorrelationsPage() {
  const [correlations, setCorrelations] = useState<Correlation[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    correlationsApi.getCorrelations()
      .then(res => setCorrelations(res.items))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Correlations" 
        description="Correlated attack sequences linking multiple security signals."
      />
      
      <div className="rounded-md border border-zinc-800 bg-zinc-900">
        <Table>
          <TableHeader className="bg-zinc-950/50">
            <TableRow className="border-zinc-800 hover:bg-transparent">
              <TableHead className="text-zinc-400">Severity</TableHead>
              <TableHead className="text-zinc-400">Risk</TableHead>
              <TableHead className="text-zinc-400">Correlation</TableHead>
              <TableHead className="text-zinc-400">Status</TableHead>
              <TableHead className="text-zinc-400">Last Event</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow className="border-zinc-800 hover:bg-zinc-800/50">
                <TableCell colSpan={5} className="h-32 text-center text-zinc-500">
                  Loading correlations...
                </TableCell>
              </TableRow>
            ) : correlations.length === 0 ? (
              <TableRow className="border-zinc-800 hover:bg-zinc-800/50">
                <TableCell colSpan={5} className="h-32 text-center text-zinc-500">
                  No correlations detected
                </TableCell>
              </TableRow>
            ) : (
              correlations.map(corr => (
                <TableRow key={corr.id} className="border-zinc-800 hover:bg-zinc-800/50 cursor-pointer">
                  <TableCell>
                    <Badge variant={
                      corr.severity === 'CRITICAL' ? 'destructive' :
                      corr.severity === 'HIGH' ? 'destructive' :
                      corr.severity === 'MEDIUM' ? 'warning' : 'secondary'
                    }>{corr.severity}</Badge>
                  </TableCell>
                  <TableCell>
                    {corr.risk_level ? (
                      <div className="flex flex-col">
                        <span className="font-medium">{corr.risk_level}</span>
                        <span className="text-xs text-zinc-500">{corr.risk_score}/100</span>
                      </div>
                    ) : (
                      <span className="text-zinc-500">Unscored</span>
                    )}
                  </TableCell>
                  <TableCell>
                    <Link href={`/correlations/${corr.id}`} className="font-medium hover:underline">
                      {corr.name}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{corr.status}</Badge>
                  </TableCell>
                  <TableCell className="text-zinc-400">
                    {format(new Date(corr.last_event_at), 'MMM d, HH:mm:ss')}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
