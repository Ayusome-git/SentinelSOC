"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getIndicators, lookupIndicator } from "@/lib/api/threat_intel";
import { 
  Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, AlertTriangle, ShieldCheck, ShieldAlert, Loader2, Info } from "lucide-react";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";

export default function ThreatIntelligencePage() {
  const [lookupValue, setLookupValue] = useState("");
  const [lookupType, setLookupType] = useState("IP_ADDRESS");
  const [isLookingUp, setIsLookingUp] = useState(false);
  const [lookupResult, setLookupResult] = useState<any>(null);
  
  const { data: indicatorsData, isLoading } = useQuery({
    queryKey: ["threat_indicators"],
    queryFn: () => getIndicators({ page_size: 10 })
  });

  const handleLookup = async () => {
    if (!lookupValue) return;
    setIsLookingUp(true);
    setLookupResult(null);
    try {
      const result = await lookupIndicator({ indicator: lookupValue, indicator_type: lookupType });
      setLookupResult(result);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLookingUp(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Threat Intelligence</h1>
        <p className="text-muted-foreground mt-2">
          Configure threat intelligence providers and perform manual lookups.
        </p>
      </div>
      
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Search className="h-5 w-5" />
              <span>Manual Indicator Lookup</span>
            </CardTitle>
            <CardDescription>Query an indicator against configured providers</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex space-x-2">
              <Select value={lookupType} onValueChange={(v) => setLookupType(v || "ip")}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="IP_ADDRESS">IP Address</SelectItem>
                  <SelectItem value="DOMAIN">Domain</SelectItem>
                  <SelectItem value="URL">URL</SelectItem>
                  <SelectItem value="HASH_SHA256">SHA256</SelectItem>
                </SelectContent>
              </Select>
              <Input 
                placeholder="Enter indicator value..." 
                value={lookupValue}
                onChange={(e) => setLookupValue(e.target.value)}
              />
              <Button onClick={handleLookup} disabled={isLookingUp || !lookupValue}>
                {isLookingUp ? <Loader2 className="h-4 w-4 animate-spin" /> : "Lookup"}
              </Button>
            </div>
            
            {lookupResult && (
              <div className="mt-4 pt-4 border-t">
                {lookupResult.found ? (
                  <Alert variant={lookupResult.malicious ? "destructive" : "default"}>
                    {lookupResult.malicious ? <ShieldAlert className="h-4 w-4" /> : <ShieldCheck className="h-4 w-4" />}
                    <AlertTitle>
                      {lookupResult.malicious ? "Malicious Indicator" : "Benign Indicator"} (Score: {lookupResult.confidence})
                    </AlertTitle>
                    <AlertDescription className="mt-2">
                      <div className="text-sm space-y-1">
                        <div><strong>Source:</strong> {lookupResult.source}</div>
                        {lookupResult.categories && lookupResult.categories.length > 0 && (
                          <div>
                            <strong>Categories:</strong>{" "}
                            {lookupResult.categories.map((c: string) => (
                              <Badge key={c} variant="outline" className="mr-1">{c}</Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </AlertDescription>
                  </Alert>
                ) : (
                  <Alert>
                    <Info className="h-4 w-4" />
                    <AlertTitle>No Match Found</AlertTitle>
                    <AlertDescription>
                      The indicator was not found in the Threat Intelligence provider databases.
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            )}
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Recent Intel Detections</CardTitle>
            <CardDescription>Recently identified malicious indicators</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex justify-center p-4">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : indicatorsData?.items && indicatorsData.items.length > 0 ? (
              <div className="space-y-4">
                {indicatorsData.items.filter(i => i.malicious).slice(0, 5).map(item => (
                  <div key={item.id} className="flex justify-between items-center border-b pb-2 last:border-0 last:pb-0">
                    <div>
                      <div className="font-medium font-mono text-sm">{item.indicator}</div>
                      <div className="text-xs text-muted-foreground flex items-center mt-1">
                        <Badge variant="outline" className="text-[10px] py-0 mr-2">{item.indicator_type}</Badge>
                        Source: {item.source}
                      </div>
                    </div>
                    <Badge variant="destructive">Conf: {item.confidence}</Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center p-4 text-muted-foreground border rounded-md border-dashed">
                No recent malicious indicators found.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
