import { ReactNode } from 'react'

export default function PageTitle({
  title,
  subtitle,
  right,
}: {
  title: string
  subtitle?: string
  right?: ReactNode
}) {
  return (
    <div className="flex items-end justify-between gap-4 mb-8">
      <div>
        <h1 className="font-title text-3xl md:text-4xl font-bold text-ink tracking-wider">
          {title}
        </h1>
        {subtitle && (
          <div className="mt-2 text-sm text-ink-light tracking-wider">{subtitle}</div>
        )}
        <div className="mt-3 w-16 h-[3px] bg-cinnabar rounded-full" />
      </div>
      {right && <div>{right}</div>}
    </div>
  )
}
