import { useEffect, useState } from 'react'

/** 打字机效果 — 把 full 文本逐字暴露出来 */
export function useTypewriter(full: string, speed = 28) {
  const [shown, setShown] = useState('')
  const [done, setDone] = useState(false)

  useEffect(() => {
    setShown('')
    setDone(false)
    if (!full) {
      setDone(true)
      return
    }
    let i = 0
    const id = setInterval(() => {
      i += 1
      setShown(full.slice(0, i))
      if (i >= full.length) {
        clearInterval(id)
        setDone(true)
      }
    }, speed)
    return () => clearInterval(id)
  }, [full, speed])

  return { shown, done }
}
