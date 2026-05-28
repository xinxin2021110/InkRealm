import { Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Trash2, MessageSquarePlus, Clock } from 'lucide-react'
import { chatApi } from '../api/chat'
import LoadingScroll from '../components/LoadingScroll'
import ErrorView from '../components/ErrorView'
import PageTitle from '../components/PageTitle'

export default function ChatSessions() {
  const nav = useNavigate()
  const qc = useQueryClient()

  const { data: sessions = [], isLoading, error, refetch } = useQuery({
    queryKey: ['chat-sessions'],
    queryFn: chatApi.listSessions,
  })

  const remove = useMutation({
    mutationFn: chatApi.deleteSession,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['chat-sessions'] }),
  })

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <PageTitle
        title="墨笺对谈"
        subtitle="此处珍藏与诸般书中人物的笔谈"
        right={
          <Link to="/library" className="btn-cinnabar">
            <MessageSquarePlus className="w-4 h-4" />
            发起新对谈
          </Link>
        }
      />

      {isLoading && <LoadingScroll text="检索往日笔谈…" />}
      {error && <ErrorView message={(error as Error).message} onRetry={() => refetch()} />}

      {!isLoading && sessions.length === 0 && (
        <div className="text-center py-20">
          <div className="text-5xl mb-3">🪶</div>
          <div className="text-ink-light mb-4">尚无对谈记录</div>
          <Link to="/library" className="btn-primary">
            前去书架,寻一位心仪角色
          </Link>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {sessions.map((s, i) => (
          <motion.div
            key={s.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.05 * i }}
            onClick={() => nav(`/chat/${s.id}`)}
            className="scroll-card p-5 cursor-pointer group"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="font-title text-lg font-bold text-ink tracking-wider">
                {s.character_name}
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  if (confirm('删除此对谈?')) remove.mutate(s.id)
                }}
                className="opacity-0 group-hover:opacity-100 transition text-ink-light/60 hover:text-cinnabar"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
            <div className="text-xs text-ink-light tracking-wider mb-3">
              来自《{s.novel_title}》 · 共 {s.message_count} 句
            </div>
            <div className="text-sm text-ink-light/85 line-clamp-2 mb-3 min-h-[2.5em]">
              {s.last_message_preview || '——'}
            </div>
            <div className="flex items-center gap-1.5 text-[11px] text-ink-light/70">
              <Clock className="w-3 h-3" />
              {new Date(s.updated_at).toLocaleString('zh-CN', { hour12: false })}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
