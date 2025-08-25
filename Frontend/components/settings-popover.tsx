"use client"

import { useState, useRef, useEffect } from "react"
import { Settings } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface SettingsPopoverProps {
  databaseUrl: string
  onDatabaseUrlChange: (url: string) => void
}

export function SettingsPopover({ databaseUrl, onDatabaseUrlChange }: SettingsPopoverProps) {
  const [tempUrl, setTempUrl] = useState(databaseUrl)
  const [isOpen, setIsOpen] = useState(false)
  const popoverRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setTempUrl(databaseUrl) // Reset on outside click
      }
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside)
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [isOpen, databaseUrl])

  const handleConfirm = async () => {
    if (!tempUrl.trim()) return;

    try {
      console.log("Sending POST to backend:", databaseUrl);

      // Send new DB URI to backend
      const response = await fetch("http://localhost:8000/set-db-uri", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_db_uri: tempUrl }),
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Failed to set DB_URI");

      console.log("Updated DB_URI:", data.DB_URI);
      onDatabaseUrlChange(tempUrl); // update parent state
      setIsOpen(false);
    } catch (err) {
      console.error("Error updating DB_URI:", err);
      alert("Failed to update database URL. Check console.");
    }
  };


  const handleCancel = () => {
    setTempUrl(databaseUrl)
    setIsOpen(false)
  }

  return (
    <div className="relative" ref={popoverRef}>
      <Button variant="ghost" size="icon" onClick={() => setIsOpen(!isOpen)}>
        <Settings className="h-5 w-5" />
        <span className="sr-only">Settings</span>
      </Button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg p-4 z-50">
          <div className="space-y-4">
            <div className="space-y-2">
              <h4 className="font-medium leading-none">Settings</h4>
              <p className="text-sm text-gray-600">Configure your database URL</p>
            </div>
            <div className="space-y-2">
              <label htmlFor="settings-database-url" className="text-sm font-medium">
                Database URL
              </label>
              <Input
                id="settings-database-url"
                type="url"
                placeholder="https://your-database-url.com"
                value={tempUrl}
                onChange={(e) => setTempUrl(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleConfirm} disabled={!tempUrl.trim()} className="flex-1">
                Confirm
              </Button>
              <Button onClick={handleCancel} variant="outline" className="flex-1 bg-transparent">
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
