import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  Download,
  Heart,
  RefreshCw,
  TrendingUp,
  CheckCheck,
  Sparkles,
} from 'lucide-react'
import { storiesApi } from '../api/stories'
import LoadingScroll from '../components/LoadingScroll'
import ErrorView from '../components/ErrorView'
import type { ChapterOut, ChoiceOptionOut } from '../types'

export default function ChapterReader() {
  const { storyId } = useParams<{ storyId: string }>()
  const id = Number(storyId)
  const nav = useNavigate()
  const qc = useQueryClient()

  const [readingIdx, setReadingIdx] = useState<number>(0) // 当前阅读章节序号 - 1
  const [showChoices, setShowChoices] = useState(false)
  const proseRef = useRef<HTMLDivElement>(null)

  const { data: story, isLoading, error, refetch } = useQuery({
    queryKey: ['story', id],
    queryFn: () => storiesApi.detail(id),
    enabled: Number.isFinite(id),
  })

  // 切换到最新章
  useEffect(() => {
    if (story && story.chapters.length > 0) {
      setReadingIdx(story.chapters.length - 1)
    }
  }, [story?.chapters?.length])

  const choose = useMutation({
    mutationFn: ({ chapterNumber, optionId }: { chapterNumber: number; optionId: string }) =>
      storiesApi.choose(id, chapterNumber, optionId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['story', id] })
      qc.invalidateQueries({ queryKey: ['stories'] })
      setShowChoices(false)
      // 滚到顶
      proseRef.current?.scrollTo({ top: 0, behavior: 'smooth' })
    },
  })

  const regen = useMutation({
    mutationFn: (chapterNumber: number) => storiesApi.regenerate(id, chapterNumber),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['story', id] })
      proseRef.current?.scrollTo({ top: 0, behavior: 'smooth' })
    },
  })

  if (isLoading) return <LoadingScroll text="正在展开章卷…" />
  if (error) return <ErrorView message={(error as Error).message} onRetry={() => refetch()} />
  if (!story) return null

  const chapter: ChapterOut | undefined = story.chapters[readingIdx]
  if (!chapter) {
    return (
      <div className="text-center py-20">
        <div className="text-ink-light">本故事尚无章节</div>
      </div>
    )
  }

  const isLatest = readingIdx === story.chapters.length - 1
  const choices = chapter.choices
  const isFinished = story.status === 'finished'

  const onChoose = (optionId: string) => {
    choose.mutate({ chapterNumber: chapter.chapter_number, optionId })
  }

  return (
    <div className="flex h-[calc(100vh-65px)]">
      {/* 左侧:故事信息栏 */}
      <aside className="w-72 flex-shrink-0 bg-cream/50 border-r border-ink/10 overflow-y-auto p-5 hidden lg:block">
        <button
          onClick={() => nav('/stories')}
          className="text-sm text-ink-light hover:text-ink inline-flex items-center gap-1.5 mb-5"
        >
          <ArrowLeft className="w-4 h-4" /> 我的故事
        </button>

        <div className="font-title text-lg font-bold text-ink tracking-widest line-clamp-2">
          《{story.title}》
        </div>
        <div className="text-xs text-ink-light tracking-widest mt-0.5">{story.theme}</div>

        <div className="mt-5 ancient-page rounded p-4 text-center">
          <div className="font-kai text-2xl text-ink">{story.user_persona_name}</div>
          <div className="text-[11px] text-ink-light tracking-widest mt-0.5">
            {story.user_persona.background}
          </div>
        </div>

        <div className="mt-5 text-xs space-y-3">
          <Stat
            icon={<TrendingUp className="w-3.5 h-3.5 text-bamboo" />}
            label="实力"
            value={story.user_power_level}
          />
          {Object.entries(story.relationship_meter).map(([name, value]) => (
            <Stat
              key={name}
              icon={<Heart className="w-3.5 h-3.5 text-cinnabar" />}
              label={`与${name}`}
              value={
                <RelationBadge value={value} />
              }
            />
          ))}
          <Stat
            icon={<CheckCheck className="w-3.5 h-3.5 text-gold" />}
            label="进度"
            value={`${story.current_chapter} / ${story.total_chapters}`}
          />
        </div>

        {/* 章节列表 */}
        <div className="mt-6">
          <div className="font-title text-xs text-ink-light tracking-widest mb-2">
            目录
          </div>
          <div className="space-y-1">
            {story.chapters.map((c, i) => (
              <button
                key={c.chapter_number}
                onClick={() => setReadingIdx(i)}
                className={`w-full text-left text-sm px-2.5 py-1.5 rounded transition
                  ${
                    i === readingIdx
                      ? 'bg-cinnabar/12 text-cinnabar font-title'
                      : 'text-ink-light hover:bg-cream hover:text-ink'
                  }`}
              >
                <span className="text-[11px] mr-2">第{c.chapter_number}章</span>
                <span className="truncate">{c.title}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="mt-6 space-y-2">
          <a
            href={storiesApi.exportUrl(id)}
            className="btn-ghost w-full text-sm"
            download
          >
            <Download className="w-4 h-4" /> 导出全文
          </a>
        </div>
      </aside>

      {/* 主阅读区 */}
      <div className="flex-1 flex flex-col">
        <div className="px-6 py-3 border-b border-ink/10 bg-cream/40 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setReadingIdx((i) => Math.max(0, i - 1))}
              disabled={readingIdx === 0}
              className="btn-ghost py-1.5 px-2 disabled:opacity-30"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <div className="font-title text-ink tracking-widest">
              第 {chapter.chapter_number} 章 · {chapter.title}
            </div>
            <button
              onClick={() => setReadingIdx((i) => Math.min(story.chapters.length - 1, i + 1))}
              disabled={readingIdx >= story.chapters.length - 1}
              className="btn-ghost py-1.5 px-2 disabled:opacity-30"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                if (confirm(`重新生成本章?(本章选择将清空)`)) {
                  regen.mutate(chapter.chapter_number)
                }
              }}
              disabled={regen.isPending}
              className="btn-ghost py-1.5 px-3 text-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${regen.isPending ? 'animate-spin' : ''}`} />
              重写
            </button>
          </div>
        </div>

        <div ref={proseRef} className="flex-1 overflow-y-auto py-10">
          <article className="ancient-page rounded-md mx-6 lg:mx-auto max-w-3xl p-10 md:p-14">
            <h2 className="text-center font-title text-3xl font-black text-cinnabar tracking-widest mb-2">
              第 {chapter.chapter_number} 章
            </h2>
            <h3 className="text-center font-title text-2xl text-ink mb-2 tracking-wider">
              {chapter.title}
            </h3>
            <div className="w-20 h-[3px] mx-auto bg-cinnabar rounded-full mb-8" />

            <div className="chapter-prose">
              {chapter.content
                .split(/\n+/)
                .filter(Boolean)
                .map((para, i) => {
                  // 跳过开头的第X章重复
                  if (i === 0 && /^第.*章/.test(para)) return null
                  return <p key={i}>{para}</p>
                })}
            </div>

            {chapter.summary && (
              <div className="mt-10 pt-6 border-t border-ink/15 text-sm text-ink-light/85">
                <div className="font-title text-cinnabar mb-1 tracking-widest">【本章纪要】</div>
                <div className="leading-relaxed">{chapter.summary}</div>
              </div>
            )}
          </article>

          {/* —— 互动选项 —— */}
          {isLatest && choices && !chapter.user_choice && !choose.isPending && (
            <div className="max-w-3xl mx-6 lg:mx-auto mt-8">
              <button
                onClick={() => setShowChoices(true)}
                className="w-full py-4 rounded-md bg-cinnabar text-rice
                           font-title font-bold tracking-widest text-base shadow-scroll
                           hover:bg-cinnabar-deep transition"
              >
                <Sparkles className="inline w-4 h-4 mr-1.5" />
                本章已尽,落子何处? · 揭示选择
              </button>
            </div>
          )}

          {chapter.user_choice && !isFinished && (
            <div className="max-w-3xl mx-6 lg:mx-auto mt-6 ancient-page rounded p-4 text-center">
              <div className="text-xs text-ink-light tracking-widest mb-1">本章你已选择</div>
              <div className="font-title text-cinnabar">
                选项 {chapter.user_choice}
              </div>
            </div>
          )}

          {isFinished && readingIdx === story.chapters.length - 1 && (
            <div className="max-w-3xl mx-6 lg:mx-auto mt-8 ancient-page rounded p-8 text-center">
              <div className="text-5xl mb-3">🪷</div>
              <div className="font-title text-2xl text-ink mb-2 tracking-widest">
                故事已圆满落幕
              </div>
              <div className="text-sm text-ink-light mb-5 leading-relaxed">
                《{story.title}》 共 {story.total_chapters} 章, 与{story.target_character}的旅程已尽。
                <br />
                可在左侧导出全文留作纪念。
              </div>
              <a href={storiesApi.exportUrl(id)} className="btn-cinnabar" download>
                <Download className="w-4 h-4" /> 导出整本故事
              </a>
            </div>
          )}
        </div>
      </div>

      {/* —— 选项弹层 —— */}
      <AnimatePresence>
        {showChoices && choices && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowChoices(false)}
              className="fixed inset-0 bg-ink/50 z-40"
            />
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 30 }}
              transition={{ type: 'spring', damping: 22 }}
              className="fixed inset-0 z-50 flex items-center justify-center p-6 pointer-events-none"
            >
              <div className="ancient-page rounded-md w-full max-w-3xl p-8 max-h-[90vh] overflow-y-auto pointer-events-auto">
                <div className="text-center mb-6">
                  <div className="text-xs text-cinnabar tracking-widest mb-1 font-title">
                    第 {chapter.chapter_number} 章 · 落子之时
                  </div>
                  <div className="font-title text-2xl text-ink tracking-widest">
                    本章已尽,你的选择是?
                  </div>
                  {choices.situation_summary && (
                    <div className="mt-2 text-sm text-ink-light/85 max-w-xl mx-auto">
                      {choices.situation_summary}
                    </div>
                  )}
                </div>

                <div className="space-y-3">
                  {choices.options.map((opt) => (
                    <ChoiceCard key={opt.option_id} opt={opt} onPick={() => onChoose(opt.option_id)} />
                  ))}
                </div>

                <div className="mt-6 text-center">
                  <button
                    onClick={() => setShowChoices(false)}
                    className="btn-ghost text-xs"
                  >
                    再读一遍本章
                  </button>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {(choose.isPending || regen.isPending) && (
        <div className="fixed inset-0 bg-rice/85 z-[60] flex items-center justify-center backdrop-blur-sm">
          <LoadingScroll
            text={choose.isPending ? '正在书写下一章…' : '正在重新落墨…'}
            hint="LLM 正在按你的选择调整剧情走向,约 20-40 秒"
          />
        </div>
      )}
    </div>
  )
}

function ChoiceCard({
  opt,
  onPick,
}: {
  opt: ChoiceOptionOut
  onPick: () => void
}) {
  const relSum = Object.values(opt.relationship_change || {}).reduce(
    (a, b) => a + b,
    0,
  )
  return (
    <button onClick={onPick} className="choice-card">
      <div className="choice-letter">{opt.option_id}</div>
      <div className="font-title text-base font-bold text-ink mb-1.5 pl-7">
        {opt.text}
      </div>
      {opt.description && (
        <div className="text-sm text-ink-light leading-relaxed pl-7 mb-2">
          {opt.description}
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2 pl-7 text-xs">
        {opt.impact && (
          <Mini label="剧情影响" value={opt.impact} tone="bamboo" />
        )}
        {opt.risk && <Mini label="风险" value={opt.risk} tone="cinnabar" />}
        {relSum !== 0 && (
          <Mini
            label="关系变化"
            value={`${relSum > 0 ? '+' : ''}${relSum}`}
            tone={relSum > 0 ? 'bamboo' : 'cinnabar'}
          />
        )}
      </div>
    </button>
  )
}

function Mini({
  label,
  value,
  tone,
}: {
  label: string
  value: string
  tone: 'bamboo' | 'cinnabar'
}) {
  return (
    <div
      className={`px-2 py-1 rounded border-l-2
        ${tone === 'bamboo'
          ? 'border-bamboo bg-bamboo/5 text-bamboo'
          : 'border-cinnabar bg-cinnabar/5 text-cinnabar'
        }`}
    >
      <div className="text-[10px] tracking-widest opacity-70">{label}</div>
      <div className="font-title">{value}</div>
    </div>
  )
}

function Stat({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-2 px-2 py-1.5 rounded bg-cream/60">
      <span className="inline-flex items-center gap-1.5 text-ink-light tracking-widest">
        {icon}
        {label}
      </span>
      <span className="font-title text-ink">{value}</span>
    </div>
  )
}

function RelationBadge({ value }: { value: number }) {
  const tag = value >= 60 ? '亲密' : value >= 30 ? '友好' : value > 0 ? '中立' : value > -30 ? '冷淡' : '敌对'
  const tone =
    value >= 30 ? 'text-bamboo' : value > 0 ? 'text-ink' : 'text-cinnabar'
  return (
    <span className={tone}>
      {value} <span className="text-[10px] opacity-70">({tag})</span>
    </span>
  )
}
