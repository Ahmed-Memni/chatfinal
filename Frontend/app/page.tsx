"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { MessageCircle } from "lucide-react"
import { VermegIcon } from "@/components/vermeg-icon"
import { ChatInterface } from "@/components/chat-interface"

export default function Home() {
  const [databaseUrl, setDatabaseUrl] = useState("")
  const [isConfigured, setIsConfigured] = useState(false)

  const handleConfigure = async () => {
    if (!databaseUrl.trim()) return;

    try {
      console.log("Sending POST to backend:", databaseUrl);

      const response = await fetch("http://localhost:8000/set-db-uri", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_db_uri: databaseUrl }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Failed to set DB_URI");

      console.log("Updated DB_URI:", data.DB_URI);
      setIsConfigured(true);  // proceed to chat interface
    } catch (err) {
      console.error("Error updating DB_URI:", err);
      alert("Failed to update database URL. Check console.");
    }
  };
  if (isConfigured) {
    return <ChatInterface databaseUrl={databaseUrl} onReconfigure={() => setIsConfigured(false)} />
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="flex h-16 items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <VermegIcon className="h-8 w-8" />
            <h1 className="text-xl font-semibold text-foreground">Vermeg Assistant</h1>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex min-h-[calc(100vh-4rem)] items-center justify-center p-6">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-blue-100">
              <MessageCircle className="h-8 w-8 text-blue-600" />
            </div>

            <CardTitle className="text-2xl">Welcome to Vermeg Assistant</CardTitle>
            <CardDescription>Configure your database connection to get started with the chatbot</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="database-url" className="text-sm font-medium text-foreground">
                Database URL
              </label>
              <Input
                id="database-url"
                type="url"
                placeholder="https://your-database-url.com"
                value={databaseUrl}
                onChange={(e) => setDatabaseUrl(e.target.value)}
                className="w-full border border-blue-400 focus:border-blue-600 focus:ring-blue-600 placeholder-blue-300"
              />
            </div>
            <Button onClick={handleConfigure} disabled={!databaseUrl.trim()} className="w-full bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-300">
              Start Chatting
            </Button>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
