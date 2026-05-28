import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft,
  Send,
  Download,
  Info,
  Trash2,
  X,
  Crown,
  Quote,
} from 'lucide-react'
import { chatApi } from '../api/chat'
import { novelsApi } from '../api/novels'
import LoadingScroll from '../components/LoadingScroll'
import ErrorView from '../components/ErrorView'
import type { ChatMessageOut } from '../types'

function MessageBubble({
  msg,
  characterName,
  characterAvatar,
  userName,
  liveOverrideContent,
  showCursor,
}: {
  msg: ChatMessageOut
  characterName: string
  characterAvatar: string
  userName: string
  /** 流式过程中覆盖 msg.content，用真正流回来的文本渲染 */
  liveOverrideContent?: string | null
  /** 是否在末尾显示打字光标（仍在流） */
  showCursor?: boolean
}) {
  const isUser = msg.role === 'user'
  const display = !isUser && liveOverrideContent != null ? liveOverrideContent : msg.content

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      {!isUser && (
        <div className="flex-shrink-0 w-11 h-11 rounded-full bg-gradient-to-br from-cream to-lotus
                        border-2 border-ink/20 flex items-center justify-center text-2xl shadow-inner">
          {characterAvatar}
        </div>
      )}
      <div className={`max-w-[72%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        <div className={`text-[11px] tracking-widest ${isUser ? 'text-right' : ''} text-ink-light/70`}>
          {isUser ? userName : characterName}
          {!isUser && msg.retrieved_quotes > 0 && (
            <span className="ml-2 text-cinnabar/70">
              ⊙ 检索 {msg.retrieved_memories} 记忆 · {msg.retrieved_quotes} 语录
            </span>
          )}
        </div>
        {isUser ? (
          <div className="bamboo-bubble px-5 py-3 font-kai text-base">{display}</div>
        ) : (
          <div className="scroll-bubble font-body text-base">
            {display}
            {showCursor && <span className="inline-block w-1.5 h-4 bg-ink ml-0.5 animate-pulse" />}
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default function ChatPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const id = Number(sessionId)
  const nav = useNavigate()
  const qc = useQueryClient()

  const [draft, setDraft] = useState('')
  const [showProfile, setShowProfile] = useState(false)
  const scrollerRef = useRef<HTMLDivElement>(null)

  // —— 流式状态 ——
  const [streaming, setStreaming] = useState(false)
  const [streamDelta, setStreamDelta] = useState('') // 流过程中拼接的角色回复
  const [streamUserId, setStreamUserId] = useState<number | null>(null) // 临时占位的 user msg id
  const [streamPendingChar, setStreamPendingChar] = useState(false) // 是否需要在最新一条 assistant 上覆盖

  const { data: session, isLoading, error, refetch } = useQuery({
    queryKey: ['chat-session', id],
    queryFn: () => chatApi.getSession(id),
    enabled: Number.isFinite(id),
  })

  const { data: character } = useQuery({
    queryKey: ['character', session?.character_id],
    queryFn: () => novelsApi.characterDetail(session!.character_id),
    enabled: !!session?.character_id,
  })

  const remove = useMutation({
    mutationFn: () => chatApi.deleteSession(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['chat-sessions'] })
      nav('/chat')
    },
  })

  useEffect(() => {
    scrollerRef.current?.scrollTo({
      top: scrollerRef.current.scrollHeight,
      behavior: 'smooth',
    })
  }, [session?.messages?.length, streaming, streamDelta])

  if (isLoading) return <LoadingScroll text="正在展开往日卷轴…" />
  if (error) return <ErrorView message={(error as Error).message} onRetry={() => refetch()} />
  if (!session) return null

  const onSend = async () => {
    const text = draft.trim()
    if (!text || streaming) return
    setDraft('')
    setStreaming(true)
    setStreamDelta('')
    setStreamUserId(null)
    setStreamPendingChar(true)
    try {
      await chatApi.sendStream(id, text, (evt) => {
        if (evt.type === 'user_message') {
          setStreamUserId(evt.message.id)
        } else if (evt.type === 'chunk') {
          setStreamDelta((s) => s + evt.delta)
        } else if (evt.type === 'done') {
          // 最终落库；让 react-query 拉一次以同步 message id / 统计
          qc.invalidateQueries({ queryKey: ['chat-session', id] })
          qc.invalidateQueries({ queryKey: ['chat-sessions'] })
        } else if (evt.type === 'error') {
          throw new Error(evt.message)
        }
      })
    } catch (e: any) {
      console.error(e)
      alert(`流式聊天失败: ${e?.message || e}`)
    } finally {
      setStreaming(false)
      // 已 invalidate；保留 streamDelta 直到新数据回来，避免空白闪烁
      setTimeout(() => {
        setStreamDelta('')
        setStreamUserId(null)
        setStreamPendingChar(false)
      }, 300)
    }
  }

  return (
    <div className="flex h-[calc(100vh-65px)]">
      {/* 主聊天区 */}
      <div className="flex-1 flex flex-col">
        {/* 顶栏 */}
        <div className="px-6 py-3 border-b border-ink/10 bg-cream/40 flex items-center justify-between gap-3">
          <button onClick={() => nav('/chat')} className="text-ink-light hover:text-ink">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex-1 flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cream to-lotus
                            border border-ink/20 flex items-center justify-center text-xl flex-shrink-0">
              {character?.avatar_emoji || '🪶'}
            </div>
            <div className="min-w-0">
              <div className="font-title font-bold text-ink truncate tracking-wider">
                {session.character_name}
                {character?.is_protagonist && (
                  <Crown className="inline w-4 h-4 text-gold ml-1" />
                )}
              </div>
              <div className="text-[11px] text-ink-light tracking-widest">
                《{session.novel_title}》 · 与{session.user_name}笔谈
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowProfile(true)}
              className="btn-ghost py-1.5 px-3 text-xs"
            >
              <Info className="w-3.5 h-3.5" /> 角色资料
            </button>
            <a
              href={chatApi.exportUrl(id)}
              className="btn-ghost py-1.5 px-3 text-xs"
              title="导出对话"
            >
              <Download className="w-3.5 h-3.5" /> 导出
            </a>
            <button
              onClick={() => {
                if (confirm('删除整段对谈?')) remove.mutate()
              }}
              className="btn-ghost py-1.5 px-3 text-xs text-cinnabar/80 hover:text-cinnabar"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* 消息区 */}
        <div ref={scrollerRef} className="flex-1 overflow-y-auto px-6 py-8">
          <div className="max-w-3xl mx-auto space-y-6">
            {session.messages.length === 0 && (
              <div className="text-center py-12">
                <div className="text-5xl mb-3">📜</div>
                <div className="font-title text-lg text-ink mb-1">{session.character_name}已临此卷</div>
                <div className="text-sm text-ink-light">说一句话,与他/她开启对谈</div>
              </div>
            )}

            {session.messages.map((m, i) => (
              <MessageBubble
                key={m.id}
                msg={m}
                characterName={session.character_name}
                characterAvatar={character?.avatar_emoji || '🪶'}
                userName={session.user_name}
              />
            ))}

            {/* 流式过程中：模拟正在生成的角色气泡 */}
            {streamPendingChar && (
              <MessageBubble
                msg={{
                  id: -1,
                  role: 'assistant',
                  content: '',
                  retrieved_memories: 0,
                  retrieved_quotes: 0,
                  created_at: new Date().toISOString(),
                }}
                characterName={session.character_name}
                characterAvatar={character?.avatar_emoji || '🪶'}
                userName={session.user_name}
                liveOverrideContent={streamDelta || '…'}
                showCursor={streaming}
              />
            )}

            {streaming && !streamDelta && (
              <div className="flex gap-3 -mt-3">
                <div className="w-11 h-11" />
                <div className="scroll-bubble flex items-center gap-1.5 px-5 py-4">
                  <span className="w-1.5 h-1.5 rounded-full bg-ink animate-bounce" />
                  <span className="w-1.5 h-1.5 rounded-full bg-ink animate-bounce" style={{ animationDelay: '0.15s' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-ink animate-bounce" style={{ animationDelay: '0.3s' }} />
                  <span className="ml-2 text-xs text-ink-light tracking-widest">正在凝神…</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 输入区 */}
        <div className="border-t border-ink/10 bg-cream/40 px-6 py-4">
          <div className="max-w-3xl mx-auto flex items-end gap-3">
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  onSend()
                }
              }}
              rows={2}
              maxLength={500}
              placeholder={`对${session.character_name}说一句话…(Enter 发送 · Shift+Enter 换行)`}
              className="bamboo-input resize-none flex-1"
              disabled={streaming}
            />
            <button
              onClick={onSend}
              disabled={!draft.trim() || streaming}
              className="btn-cinnabar px-5 py-3 self-stretch"
              title="发送"
            >
              <Send className="w-4 h-4" />
              <span className="hidden md:inline">发送</span>
            </button>
          </div>
          <div className="max-w-3xl mx-auto mt-1 text-right text-[11px] text-ink-light/60">
            {draft.length}/500
          </div>
        </div>
      </div>

      {/* 角色资料抽屉 */}
      <AnimatePresence>
        {showProfile && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowProfile(false)}
              className="fixed inset-0 bg-ink/30 z-40"
            />
            <motion.aside
              initial={{ x: 400, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 400, opacity: 0 }}
              transition={{ type: 'spring', damping: 25 }}
              className="fixed right-0 top-0 bottom-0 w-full md:w-[420px] z-50
                         bg-cream border-l border-ink/15 overflow-y-auto"
            >
              <div className="sticky top-0 bg-cream/95 backdrop-blur border-b border-ink/10 p-4 flex items-center justify-between">
                <div className="font-title text-lg text-ink tracking-widest">角色资料</div>
                <button
                  onClick={() => setShowProfile(false)}
                  className="text-ink-light hover:text-ink"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              {character ? (
                <div className="p-6 space-y-6">
                  <div className="text-center">
                    <div className="w-24 h-24 rounded-full mx-auto bg-gradient-to-br from-cream to-lotus
                                    border-2 border-ink/20 flex items-center justify-center text-5xl">
                      {character.avatar_emoji}
                    </div>
                    <div className="mt-3 font-title text-xl font-bold text-ink tracking-widest">
                      {character.name}
                    </div>
                    <div className="text-xs text-ink-light tracking-widest">
                      《{character.book_title}》
                    </div>
                  </div>

                  <Section title="性格特征">
                    <Tags items={character.personality_traits} />
                  </Section>
                  <Section title="说话风格">
                    <Tags items={character.speech_style} />
                  </Section>
                  <Section title="关键动机">
                    <Tags items={character.key_motivations} />
                  </Section>

                  <Section title="人物关系">
                    <div className="space-y-2">
                      {character.relationships.slice(0, 8).map((r, i) => (
                        <div key={i} className="text-sm border-l-2 border-ink/20 pl-3">
                          <div className="font-title text-ink">
                            {r.name} <span className="text-ink-light text-xs">({r.relation})</span>
                          </div>
                          <div className="text-xs text-ink-light/85 line-clamp-2">{r.interaction}</div>
                        </div>
                      ))}
                    </div>
                  </Section>

                  <Section title="经典语录" icon={<Quote className="w-3.5 h-3.5" />}>
                    <div className="space-y-2">
                      {character.sample_quotes.map((q, i) => (
                        <div
                          key={i}
                          className="text-sm font-kai text-ink/90 bg-cream/70 px-3 py-2 rounded
                                     border-l-2 border-cinnabar/40 italic"
                        >
                          "{q}"
                        </div>
                      ))}
                    </div>
                  </Section>
                </div>
              ) : (
                <LoadingScroll text="正在拓印资料…" />
              )}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}

function Section({
  title,
  children,
  icon,
}: {
  title: string
  children: React.ReactNode
  icon?: React.ReactNode
}) {
  return (
    <div>
      <div className="flex items-center gap-1.5 font-title text-sm text-ink mb-2 tracking-widest">
        {icon}
        【{title}】
      </div>
      {children}
    </div>
  )
}

function Tags({ items }: { items: string[] }) {
  if (!items?.length) return <div className="text-xs text-ink-light">——</div>
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((t, i) => (
        <span
          key={i}
          className="text-xs px-2 py-0.5 rounded-sm bg-ink/5 text-ink-light border border-ink/10"
        >
          {t}
        </span>
      ))}
    </div>
  )
}
