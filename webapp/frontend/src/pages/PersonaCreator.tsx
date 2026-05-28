import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { Check, ChevronLeft, ChevronRight, Sparkles, ArrowLeft } from 'lucide-react'
import { storiesApi } from '../api/stories'
import { useStoryDraft } from '../store/storyDraft'
import LoadingScroll from '../components/LoadingScroll'
import ErrorView from '../components/ErrorView'
import type { PersonaDimension, SelectionsKey } from '../types'

type StepKey = SelectionsKey | 'name' | 'chapters'

const STEP_FLOW: { key: StepKey; label: string; description: string }[] = [
  { key: 'background', label: '出身', description: '决定你的故事起点与人际关系' },
  { key: 'personality', label: '性格', description: '与主角碰撞出的化学反应' },
  { key: 'relationship', label: '羁绊', description: '与主角的初始关系定位' },
  { key: 'ability', label: '能力', description: '你在江湖立足的根本' },
  { key: 'name', label: '取名', description: '为这位主人公,题写一个响亮名字' },
  { key: 'chapters', label: '篇幅', description: '想要书写多长的传奇' },
]

const dimKeys: SelectionsKey[] = ['background', 'personality', 'relationship', 'ability']

export default function PersonaCreator() {
  const { characterId } = useParams<{ characterId: string }>()
  const charId = Number(characterId)
  const nav = useNavigate()
  const draft = useStoryDraft()

  const [stepIdx, setStepIdx] = useState(0)
  const step = STEP_FLOW[stepIdx]

  // 1. 先确保 draft 有 novelId/characterId
  useEffect(() => {
    if (!draft.novelId || !draft.characterId) {
      // 用户直接从 URL 进入,缺少上下文 — 退回到小说库
      nav('/library')
    }
  }, [draft.novelId, draft.characterId, nav])

  const { data: dimensions, isLoading, error, refetch } = useQuery({
    queryKey: ['persona-options', draft.novelId, charId],
    queryFn: () => storiesApi.personaOptions(draft.novelId!, charId),
    enabled: !!draft.novelId && Number.isFinite(charId),
  })

  const create = useMutation({
    mutationFn: () =>
      storiesApi.create({
        novel_id: draft.novelId!,
        character_id: draft.characterId!,
        user_name: draft.userName.trim() || '林云',
        selections: draft.selections,
        total_chapters: draft.totalChapters,
      }),
    onSuccess: (s) => {
      nav(`/stories/${s.id}/outline`, { replace: true })
    },
  })

  if (isLoading) return <LoadingScroll text="正在演算多维人设…" hint="首次进入需调用大模型,稍候片刻" />
  if (error) return <ErrorView message={(error as Error).message} onRetry={() => refetch()} />
  if (!dimensions) return null

  const next = () => setStepIdx((i) => Math.min(i + 1, STEP_FLOW.length - 1))
  const prev = () => setStepIdx((i) => Math.max(i - 1, 0))

  const isLast = stepIdx === STEP_FLOW.length - 1
  const canProceed = (() => {
    if (dimKeys.includes(step.key as SelectionsKey)) {
      return !!draft.selections[step.key as SelectionsKey]
    }
    if (step.key === 'name') return draft.userName.trim().length > 0
    if (step.key === 'chapters') return draft.totalChapters >= 3 && draft.totalChapters <= 20
    return true
  })()

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <button
        onClick={() => nav(-1)}
        className="inline-flex items-center gap-1.5 text-sm text-ink-light hover:text-ink mb-6"
      >
        <ArrowLeft className="w-4 h-4" /> 返回角色页
      </button>

      {/* —— Step 指示器 —— */}
      <div className="mb-10">
        <div className="text-center mb-5">
          <div className="font-title text-2xl text-ink tracking-widest">
            为「与{draft.characterName}的故事」铺陈起笔
          </div>
          <div className="text-xs text-ink-light tracking-widest mt-1">
            来自《{draft.bookTitle}》
          </div>
        </div>
        <div className="flex items-center justify-between max-w-3xl mx-auto">
          {STEP_FLOW.map((s, i) => (
            <div key={s.key} className="flex-1 flex items-center">
              <div className="flex flex-col items-center flex-1">
                <div
                  className={`w-9 h-9 rounded-full flex items-center justify-center
                              text-sm font-title font-bold transition-all
                    ${
                      i < stepIdx
                        ? 'bg-bamboo text-rice'
                        : i === stepIdx
                        ? 'bg-cinnabar text-rice shadow-seal scale-110'
                        : 'bg-cream border border-ink/20 text-ink-light/60'
                    }`}
                >
                  {i < stepIdx ? <Check className="w-4 h-4" /> : i + 1}
                </div>
                <div
                  className={`mt-1.5 text-[11px] tracking-widest
                    ${i === stepIdx ? 'text-cinnabar font-bold' : 'text-ink-light/70'}`}
                >
                  {s.label}
                </div>
              </div>
              {i < STEP_FLOW.length - 1 && (
                <div
                  className={`flex-1 h-[2px] mb-5 mx-1
                    ${i < stepIdx ? 'bg-bamboo' : 'bg-ink/15'}`}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* —— 内容区 —— */}
      <div className="ancient-page rounded-md p-8 min-h-[420px]">
        <AnimatePresence mode="wait">
          <motion.div
            key={step.key}
            initial={{ opacity: 0, x: 16 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -16 }}
            transition={{ duration: 0.3 }}
          >
            <div className="mb-6 text-center">
              <div className="text-xs text-cinnabar tracking-widest font-title">
                第 {stepIdx + 1} 步 / 共 {STEP_FLOW.length} 步
              </div>
              <div className="font-title text-2xl font-bold text-ink mt-1 tracking-widest">
                {step.label}
              </div>
              <div className="text-sm text-ink-light mt-1">{step.description}</div>
            </div>

            {dimKeys.includes(step.key as SelectionsKey) && (
              <DimensionPicker
                dim={dimensions[step.key as SelectionsKey]}
                value={draft.selections[step.key as SelectionsKey]}
                onChange={(id) => draft.setSelection(step.key as SelectionsKey, id)}
              />
            )}

            {step.key === 'name' && (
              <div className="max-w-md mx-auto">
                <label className="block text-sm font-title text-ink mb-2 text-center tracking-widest">
                  请为你的角色取名
                </label>
                <input
                  value={draft.userName}
                  onChange={(e) => draft.setUserName(e.target.value)}
                  className="bamboo-input text-center text-xl font-kai"
                  placeholder="如:林云、萧炎、韩立…"
                  maxLength={20}
                  autoFocus
                />
                <div className="text-center text-xs text-ink-light mt-2">
                  ✦ 落笔之时,这便是你在书中的名号
                </div>
              </div>
            )}

            {step.key === 'chapters' && (
              <div className="max-w-md mx-auto">
                <label className="block text-sm font-title text-ink mb-3 text-center tracking-widest">
                  传奇有几章?
                </label>
                <input
                  type="range"
                  min={3}
                  max={20}
                  value={draft.totalChapters}
                  onChange={(e) => draft.setTotalChapters(Number(e.target.value))}
                  className="w-full accent-cinnabar"
                />
                <div className="text-center mt-3">
                  <div className="font-title text-5xl font-black text-cinnabar">
                    {draft.totalChapters}
                  </div>
                  <div className="text-xs text-ink-light tracking-widest">章</div>
                </div>
                <div className="text-center text-xs text-ink-light/80 mt-3 leading-relaxed">
                  {draft.totalChapters <= 5
                    ? '✦ 一段短章,聚焦一次相遇'
                    : draft.totalChapters <= 10
                    ? '✦ 中篇之旅,起承转合俱全'
                    : '✦ 长篇画卷,师徒山河尽在其中'}
                </div>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* 操作栏 */}
      <div className="flex items-center justify-between mt-8">
        <button
          onClick={prev}
          disabled={stepIdx === 0}
          className="btn-ghost"
        >
          <ChevronLeft className="w-4 h-4" /> 上一步
        </button>

        {!isLast ? (
          <button
            onClick={next}
            disabled={!canProceed}
            className="btn-primary"
          >
            下一步 <ChevronRight className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={() => create.mutate()}
            disabled={!canProceed || create.isPending}
            className="btn-cinnabar"
          >
            {create.isPending ? (
              <>正在落笔…</>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                生成故事大纲
              </>
            )}
          </button>
        )}
      </div>

      {create.isError && (
        <div className="mt-4 px-4 py-2 rounded bg-cinnabar/10 border border-cinnabar/30 text-cinnabar text-sm">
          {(create.error as Error).message}
        </div>
      )}
      {create.isPending && (
        <div className="mt-6">
          <LoadingScroll
            text="正在为你与TA起草大纲…"
            hint="LLM 需要 20-40 秒构思整本故事的脉络"
          />
        </div>
      )}
    </div>
  )
}

function DimensionPicker({
  dim,
  value,
  onChange,
}: {
  dim: PersonaDimension
  value: string
  onChange: (id: string) => void
}) {
  return (
    <div>
      <div className="text-center text-sm text-ink-light mb-5 leading-relaxed">
        {dim.description}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {dim.options.map((opt) => {
          const selected = value === opt.id
          return (
            <button
              key={opt.id}
              onClick={() => onChange(opt.id)}
              className={`relative text-left p-5 rounded-md border-2 transition-all
                ${
                  selected
                    ? 'border-cinnabar bg-cinnabar/8 shadow-scroll-hover -translate-y-0.5'
                    : 'border-ink/15 bg-cream/60 hover:border-cinnabar/50 hover:bg-cream'
                }`}
            >
              <div className="absolute -top-3 -left-3 w-9 h-9 rounded-full bg-ink text-rice
                              flex items-center justify-center font-title font-bold shadow-seal">
                {opt.id}
              </div>
              {selected && (
                <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-cinnabar text-rice
                                flex items-center justify-center">
                  <Check className="w-3.5 h-3.5" />
                </div>
              )}
              <div className="font-title text-lg font-bold text-ink mb-1.5 tracking-wider">
                {opt.title}
              </div>
              <div className="text-sm text-ink-light leading-relaxed mb-2">
                {opt.description}
              </div>
              {opt.implications && (
                <div className="text-xs text-cinnabar/80 italic">
                  ✦ {opt.implications}
                </div>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
