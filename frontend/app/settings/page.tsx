import { PageHeader } from "@/components/layout/PageHeader"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function SettingsPage() {
  return (
    <div className="space-y-6 max-w-4xl">
      <PageHeader 
        title="Settings" 
        description="Configure your SOC platform and integrations."
      />
      
      <div className="grid gap-6">
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-zinc-200">General Settings</CardTitle>
            <CardDescription className="text-zinc-500">
              Manage basic platform configuration.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button disabled className="bg-zinc-800 text-zinc-400 hover:bg-zinc-700">Save Changes</Button>
          </CardContent>
        </Card>
        
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-zinc-200">Security</CardTitle>
            <CardDescription className="text-zinc-500">
              Configure authentication, roles, and API keys.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button disabled className="bg-zinc-800 text-zinc-400 hover:bg-zinc-700">Manage Access</Button>
          </CardContent>
        </Card>
        
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-zinc-200">Integrations</CardTitle>
            <CardDescription className="text-zinc-500">
              Connect external services and threat intelligence feeds.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button disabled className="bg-zinc-800 text-zinc-400 hover:bg-zinc-700">View Integrations</Button>
          </CardContent>
        </Card>
        
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-zinc-200">System</CardTitle>
            <CardDescription className="text-zinc-500">
              Platform status and diagnostic logs.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button disabled className="bg-zinc-800 text-zinc-400 hover:bg-zinc-700">Download Logs</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
