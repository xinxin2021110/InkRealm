import { motion } from 'framer-motion'

export default function LoadingScroll({
  text = '正在徐徐展开卷轴…',
  hint,
}: {
  text?: string
  hint?: string
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 select-none">
      <div className="relative">
        {/* 三个墨点循环放大 */}
        <div className="flex gap-3">
          {[0, 0.2, 0.4].map((d) => (
            <motion.div
              key={d}
              className="w-3 h-3 rounded-full bg-ink"
              animate={{
                scale: [0.8, 1.4, 0.8],
                opacity: [0.4, 1, 0.4],
              }}
              transition={{ duration: 1.4, repeat: Infinity, delay: d }}
            />
          ))}
        </div>
      </div>
      <div className="mt-6 font-title text-ink tracking-widest">{text}</div>
      {hint && <div className="mt-2 text-xs text-ink-light/80">{hint}</div>}
    </div>
  )
}
