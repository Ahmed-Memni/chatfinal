import { cn } from "@/lib/utils"

interface VermegIconProps {
  className?: string
  src?: string // optional prop for the image URL
}

export function VermegIcon({ className, src }: VermegIconProps) {
  return (
    <div className={cn("flex items-center justify-center", className)}>
      <img
        src={src || "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRWoaQsZekQrsIJVzpN77pDq5CK3U6rlBmVLQ&s"} // fallback image if src not provided
        alt="Vermeg Icon"
        className="h-full w-full object-contain"
      />
    </div>
  )
}
