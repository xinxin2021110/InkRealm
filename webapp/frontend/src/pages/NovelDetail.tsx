import { useNavigate, useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, MessageCircle, PenLine, Trash2, Crown } from 'lucide-react'
import { motion } from 'framer-motion'
import { useState } from 'react'
import { novelsApi } from '../api/novels'
import { chatApi } from '../api/chat'
import { useStoryDraft } from '../store/storyDraft'
import LoadingScroll from '../components/LoadingScroll'
import ErrorView from '../components/ErrorView'

export default function NovelDetail() {
  const { novelId } = useParams<{ novelId: string }>()
  const id = Number(novelId)
  const navigate = useNavigate()
  const qc = useQueryClient()
  const setDraftMeta = useStoryDraft((s) => s.setMeta)
  const resetDraft = useStoryDraft((s) => s.reset)

  const [userName, setUserName] = useState('少侠')

  const { data: novel, isLoading, error, refetch } = useQuery({
    queryKey: ['novel', id],
    queryFn: () => novelsApi.detail(id),
    enabled: Number.isFinite(id),
  })

  const createSession = useMutation({
    mutationFn: chatApi.createSession,
    onSuccess: (s) => {
      qc.invalidateQueries({ queryKey: ['chat-sessions'] })
      navigate(`/chat/${s.id}`)
    },
  })

  const removeNovel = useMutation({
    mutationFn: () => novelsApi.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['novels'] })
      navigate('/library')
    },
  })

  if (isLoading) return <LoadingScroll />
  if (error) return <ErrorView message={(error as Error).message} onRetry={() => refetch()} />
  if (!novel) return null

  const startChat = (characterId: number) => {
    createSession.mutate({
      novel_id: novel.id,
      character_id: characterId,
      user_name: userName || '少侠',
    })
  }

  const startStory = (characterId: number, characterName: string) => {
    resetDraft()
    setDraftMeta({
      novelId: novel.id,
      characterId,
      characterName,
      bookTitle: novel.title,
    })
    navigate(`/stories/new/${characterId}`)
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <button
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-1.5 text-sm text-ink-light hover:text-ink mb-6 tracking-wider"
      >
        <ArrowLeft className="w-4 h-4" /> 回到书架
      </button>

      {/* —— 小说封面信息条 —— */}
      <div className="ancient-page rounded-md p-8 mb-8">
        <div className="flex flex-col md:flex-row gap-8 items-start">
          <div className="w-32 h-40 flex-shrink-0 rounded-md bg-gradient-to-b from-ink-light to-ink
                          flex items-center justify-center text-7xl shadow-scroll-hover">
            {novel.cover_emoji}
          </div>
          <div className="flex-1">
            <h1 className="font-title text-4xl font-black text-ink tracking-wider mb-2">
              《{novel.title}》
            </h1>
            <div className="flex items-center gap-3 mb-4">
              <span className="text-sm text-ink-light tracking-widest">
                {novel.author || '佚名'}
              </span>
              <span className="text-ink-light/40">·</span>
              <span className="seal text-xs">{novel.characters_count} 角色</span>
            </div>
            <p className="text-ink-light leading-loose">{novel.description || '——'}</p>

            <div className="mt-6 flex items-center gap-3">
              <input
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
                className="bamboo-input max-w-[200px]"
                placeholder="为自己取个称呼"
                maxLength={20}
              />
              <span className="text-xs text-ink-light/70">→ 选下方角色开始</span>
            </div>
          </div>

          <button
            onClick={() => {
              if (confirm(`确定删除《${novel.title}》及其全部数据?`)) removeNovel.mutate()
            }}
            className="text-ink-light/50 hover:text-cinnabar transition p-2"
            title="删除小说"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* —— 角色网格 —— */}
      <div className="mb-4 font-title text-xl text-ink tracking-widest">书中人物</div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {novel.characters.map((c, i) => (
          <motion.div
            key={c.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.04 * i }}
            className="scroll-card p-5"
          >
            <div className="flex items-start gap-4">
              <div className="relative">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-cream to-lotus
                                flex items-center justify-center text-3xl
                                border-2 border-ink/20 shadow-inner">
                  {c.avatar_emoji}
                </div>
                {c.is_protagonist && (
                  <Crown className="w-5 h-5 absolute -top-2 -right-1 text-gold drop-shadow" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="font-title text-lg font-bold text-ink truncate tracking-wider">
                  {c.name}
                </div>
                {c.aliases.length > 0 && (
                  <div className="text-[11px] text-ink-light tracking-wider">
                    {c.aliases.join('、')}
                  </div>
                )}
                <div className="flex gap-3 mt-1 text-[11px] text-ink-light/80">
                  <span>📚 {c.memory_count} 记忆</span>
                  <span>💬 {c.quote_count} 语录</span>
                </div>
              </div>
            </div>

            <div className="text-sm text-ink-light/85 mt-3 leading-relaxed line-clamp-3">
              {c.profile_summary || '小说中的角色'}
            </div>

            <div className="grid grid-cols-2 gap-2 mt-4">
              <button
                onClick={() => startChat(c.id)}
                disabled={createSession.isPending}
                className="btn-primary py-2 text-sm"
              >
                <MessageCircle className="w-4 h-4" />
                墨笺对谈
              </button>
              <button
                onClick={() => startStory(c.id, c.name)}
                className="btn-cinnabar py-2 text-sm"
              >
                <PenLine className="w-4 h-4" />
                共谱华章
              </button>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="mt-12 text-center">
        <Link to="/library" className="btn-ghost">
          返回小说列表
        </Link>
      </div>
    </div>
  )
}
