import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowLeft, ChevronDown, BookOpen, Play, Sparkles } from 'lucide-react'
import { storiesApi } from '../api/stories'
import LoadingScroll from '../components/LoadingScroll'
import ErrorView from '../components/ErrorView'

export default function OutlineConfirm() {
  const { storyId } = useParams<{ storyId: string }>()
  const id = Number(storyId)
  const nav = useNavigate()
  const [openIdx, setOpenIdx] = useState<number | null>(0)

  const { data: story, isLoading, error, refetch } = useQuery({
    queryKey: ['story', id],
    queryFn: () => storiesApi.detail(id),
    enabled: Number.isFinite(id),
  })

  if (isLoading) return <LoadingScroll text="正在展开故事卷轴…" />
  if (error) return <ErrorView message={(error as Error).message} onRetry={() => refetch()} />
  if (!story) return null

  const persona = story.user_persona

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <button
        onClick={() => nav('/stories')}
        className="inline-flex items-center gap-1.5 text-sm text-ink-light hover:text-ink mb-6"
      >
        <ArrowLeft className="w-4 h-4" /> 返回我的故事
      </button>

      {/* —— 故事横幅 —— */}
      <div className="ancient-page rounded-md p-8 mb-8 text-center">
        <div className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full
                        bg-cinnabar/10 border border-cinnabar/30 text-xs text-cinnabar mb-3 tracking-widest">
          <Sparkles className="w-3 h-3" /> 大纲已成 · 共 {story.total_chapters} 章
        </div>
        <h1 className="font-title text-4xl font-black text-ink mb-2 tracking-widest">
          《{story.title}》
        </h1>
        <div className="text-sm text-ink-light tracking-widest">主题:{story.theme}</div>
        <div className="mt-2 text-xs text-ink-light/80">
          源自《{story.novel_title}》 · 主角:{story.target_character}
        </div>
      </div>

      {/* —— 你的人设 —— */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
        <div className="md:col-span-1 scroll-card p-5">
          <div className="font-title text-sm text-ink mb-3 tracking-widest">【你的角色】</div>
          <div className="text-center mb-4">
            <div className="text-5xl mb-2">🪶</div>
            <div className="font-kai text-2xl text-ink">{persona.name}</div>
          </div>
          <div className="space-y-1.5 text-sm">
            <Row label="出身" value={persona.background} />
            <Row label="性格" value={persona.personality} />
            <Row label="羁绊" value={persona.relationship_to_protagonist} />
            <Row label="能力" value={persona.initial_ability} />
          </div>
        </div>

        <div className="md:col-span-2 scroll-card p-5 space-y-3">
          <Detail title="背景" body={persona.background_detail} />
          <Detail title="性格深描" body={persona.personality_detail} />
          <Detail title="与主角羁绊" body={persona.relationship_detail} />
          <Detail title="能力详述" body={persona.ability_detail} />
          {persona.story_goal && <Detail title="此行所求" body={persona.story_goal} />}
        </div>
      </div>

      {/* —— 章节大纲 —— */}
      <div className="font-title text-xl text-ink mb-3 tracking-widest flex items-center gap-2">
        <BookOpen className="w-5 h-5" /> 章节大纲
      </div>

      <div className="space-y-3 mb-10">
        {story.outline.chapters.map((c, i) => {
          const open = openIdx === i
          return (
            <div
              key={c.chapter_number}
              className={`scroll-card overflow-hidden ${open ? 'shadow-scroll-hover' : ''}`}
            >
              <button
                onClick={() => setOpenIdx(open ? null : i)}
                className="w-full flex items-center justify-between p-5 text-left"
              >
                <div className="flex items-center gap-4">
                  <div className="seal text-sm">第 {c.chapter_number} 章</div>
                  <div>
                    <div className="font-title text-lg text-ink tracking-widest">{c.title}</div>
                    {!open && (
                      <div className="text-xs text-ink-light line-clamp-1 mt-0.5">
                        {c.core_conflict}
                      </div>
                    )}
                  </div>
                </div>
                <ChevronDown
                  className={`w-5 h-5 text-ink-light transition ${open ? 'rotate-180' : ''}`}
                />
              </button>

              <AnimatePresence>
                {open && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.25 }}
                    className="px-5 pb-5 border-t border-ink/10 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm"
                  >
                    <Field label="核心冲突" value={c.core_conflict} />
                    <Field label="场景设定" value={c.scene_setting} />
                    <Field label="角色互动点" value={c.character_interaction} />
                    <Field label="剧情作用" value={c.plot_function} />
                    {c.branch_points?.length > 0 && (
                      <div className="md:col-span-2">
                        <Field
                          label="可分支点"
                          value={c.branch_points.join(' · ')}
                        />
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )
        })}
      </div>

      <div className="flex justify-end">
        <button
          onClick={() => nav(`/stories/${story.id}`)}
          className="btn-cinnabar text-base px-8 py-3"
        >
          <Play className="w-5 h-5" />
          开卷阅读 →
        </button>
      </div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-2">
      <span className="text-xs text-ink-light/70 tracking-widest w-10">{label}</span>
      <span className="text-sm text-ink flex-1">{value}</span>
    </div>
  )
}
function Detail({ title, body }: { title: string; body: string }) {
  return (
    <div>
      <div className="font-title text-sm text-cinnabar mb-1 tracking-widest">【{title}】</div>
      <div className="text-sm text-ink-light/95 leading-loose">{body}</div>
    </div>
  )
}
function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[11px] text-cinnabar tracking-widest mb-0.5">{label}</div>
      <div className="text-ink-light/95 leading-relaxed">{value || '——'}</div>
    </div>
  )
}
