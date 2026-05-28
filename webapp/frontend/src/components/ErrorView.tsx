import { AlertTriangle } from 'lucide-react'

export default function ErrorView({
  message = '出现了一些问题',
  onRetry,
}: {
  message?: string
  onRetry?: () => void
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <AlertTriangle className="w-10 h-10 text-cinnabar mb-3" />
      <div className="font-title text-ink mb-1">{message}</div>
      {onRetry && (
        <button onClick={onRetry} className="btn-ghost mt-4">
          再试一次
        </button>
      )}
    </div>
  )
}
