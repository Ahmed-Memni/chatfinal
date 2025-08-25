"use client"

import type React from "react"
import { useState, useRef, useEffect } from "react"
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send, ArrowLeft, Download, Loader2 } from "lucide-react"
import { VermegIcon } from "@/components/vermeg-icon"
import { SettingsPopover } from "@/components/settings-popover"

// ... your Message and ChatInterfaceProps interfaces here ...

export function ChatInterface({ databaseUrl, onReconfigure }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content: "Hello! I'm your Vermeg Assistant. How can I help you today?",
      isUser: false,
      timestamp: new Date(),
    },
  ])
  const [inputValue, setInputValue] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const [currentDatabaseUrl, setCurrentDatabaseUrl] = useState(databaseUrl)

  const scrollToBottom = () => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector("[data-radix-scroll-area-viewport]")
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      isUser: true,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue("")
    setIsLoading(true)

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: "user123",
          user_input: userMessage.content,
        }),
      })

      if (!response.ok) throw new Error(`Server error: ${response.status}`)

      const data = await response.json()

      let botMessage: Message

      if (data.result?.toLowerCase().includes("here is the chart of")) {
        botMessage = {
          id: (Date.now() + 1).toString(),
          content: data.result,
          isUser: false,
          timestamp: new Date(),
          hasImage: true,
          imageUrl: `http://localhost:8000/static/graph.png?timestamp=${Date.now()}&id=${Date.now()}`,
        }
      } else {
        botMessage = {
          id: (Date.now() + 1).toString(),
          content: data.result || "No response from server",
          isUser: false,
          timestamp: new Date(),
        }
      }

      setMessages((prev) => [...prev, botMessage])
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        content: `[Error] ${error}`,
        isUser: false,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const downloadImage = async (imageUrl: string) => {
    try {
      const image = new Image()
      image.crossOrigin = "anonymous"
      image.src = imageUrl

      await new Promise((resolve, reject) => {
        image.onload = resolve
        image.onerror = reject
      })

      const canvas = document.createElement("canvas")
      canvas.width = image.naturalWidth
      canvas.height = image.naturalHeight
      const ctx = canvas.getContext("2d")
      if (!ctx) return

      ctx.drawImage(image, 0, 0)

      canvas.toBlob((blob) => {
        if (!blob) return
        const url = URL.createObjectURL(blob)
        const link = document.createElement("a")
        link.href = url
        link.download = `chart-${Date.now()}.png`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
      }, "image/png")
    } catch (err) {
      console.error("Download failed", err)
    }
  }

  return (
    <div className="flex h-screen flex-col bg-background">
      <header className="border-b border-border bg-card">
        <div className="flex h-16 items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" onClick={onReconfigure}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <VermegIcon className="h-8 w-8" />
            <div>
              <h1 className="text-lg font-semibold text-foreground">Vermeg Assistant</h1>
              <p className="text-xs text-muted-foreground">Connected to database</p>
            </div>
          </div>
          <SettingsPopover databaseUrl={currentDatabaseUrl} onDatabaseUrlChange={setCurrentDatabaseUrl} />
        </div>
      </header>

      <ScrollArea ref={scrollAreaRef} className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.isUser ? "justify-end" : "justify-start"}`}>
              <Card className={`max-w-[80%] ${message.isUser ? "bg-primary text-primary-foreground" : "bg-card"}`}>
                <div className="p-4">
                  <p className="text-sm whitespace-pre-line">{message.content}</p>
                  {message.hasImage && message.imageUrl && (
                    <div className="mt-3 space-y-2">
                      <TransformWrapper>
                        <TransformComponent>
                          <div className="flex justify-center">
                            <img
                              src={message.imageUrl}
                              alt="Generated chart"
                              className="rounded-md border max-h-[400px] max-w-full object-contain"
                            />
                          </div>
                        </TransformComponent>
                      </TransformWrapper>
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full"
                        onClick={() => downloadImage(message.imageUrl)}
                      >
                        <Download className="mr-2 h-4 w-4" />
                        Download Chart
                      </Button>
                    </div>
                  )}
                  <p className="mt-2 text-xs opacity-70">{message.timestamp.toLocaleTimeString()}</p>
                </div>
              </Card>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <Card className="bg-card">
                <div className="flex items-center gap-2 p-4">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <p className="text-sm text-muted-foreground">Vermeg Assistant is typing...</p>
                </div>
              </Card>
            </div>
          )}
        </div>
      </ScrollArea>

      <div className="border-t border-border bg-card p-4">
        <div className="flex gap-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button onClick={handleSendMessage} disabled={!inputValue.trim() || isLoading} size="icon">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}