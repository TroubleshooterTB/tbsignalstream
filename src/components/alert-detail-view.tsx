
"use client"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"

interface AlertDetailViewProps {
    alert: {
        id: number;
        title: string;
        severity: string;
        timestamp: string;
        source: string;
    } | null;
    isOpen: boolean;
    onClose: () => void;
}

export function AlertDetailView({ alert, isOpen, onClose }: AlertDetailViewProps) {
  if (!alert) return null

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{alert.title}</DialogTitle>
          <DialogDescription>
            Detailed view of the alert.
          </DialogDescription>
        </DialogHeader>
        <div>
          <p><strong>ID:</strong> {alert.id}</p>
          <p><strong>Severity:</strong> {alert.severity}</p>
          <p><strong>Timestamp:</strong> {new Date(alert.timestamp).toLocaleString()}</p>
          <p><strong>Source:</strong> {alert.source}</p>
        </div>
      </DialogContent>
    </Dialog>
  )
}
