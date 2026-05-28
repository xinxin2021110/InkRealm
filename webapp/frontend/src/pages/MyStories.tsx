import { Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { BookOpen, Trash2, Download, Plus, FileEdit } from 'lucide-react'
import { storiesApi } from '../api/stories'
import LoadingScroll from '../components/LoadingScroll'
import ErrorView from '../components/ErrorView'
import PageTitle from '../components/PageTitle'

export default function MyStories() {
  const nav = useNavigate()
  const qc = useQueryClient()
  const { data: stories = [], isLoading, error, refetch } = useQuery({
    queryKey: ['stories'],
    queryFn: storiesApi.list,
  })

  const remove = useMutation({
    mutationFn: storiesApi.remove,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['stories'] }),
  })

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <PageTitle
        title="我的故事"
        subtitle="此处是与诸般主角共谱的传奇集"
        right={
          <Link to="/library" className="btn-cinnabar">
            <Plus className="w-4 h-4" />
            开启新传奇
          </Link>
        }
      />

      {isLoading && <LoadingScroll text="正在翻寻你的故事卷集…" />}
      {error && <ErrorView message={(error as Error).message} onRetry={() => refetch()} />}

      {!isLoading && stories.length === 0 && (
        <div className="ancient-page rounded-md p-12 text-center">
          <div className="text-5xl mb-4">📖</div>
          <div className="font-title text-xl text-ink mb-2 tracking-widest">尚未起笔</div>
          <div className="text-sm text-ink-light mb-6">从书架挑一位心仪角色,与TA共谱独属于你们的传奇</div>
          <Link to="/library" className="btn-primary">
            <BookOpen className="w-4 h-4" /> 前往书架
          </Link>
        </div>
      )}

      <div className="space-y-4">
        {stories.map((s, i) => (
          <motion.div
            key={s.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.04 * i }}
            className="scroll-card p-5 flex flex-col md:flex-row gap-5"
          >
            <div className="flex-shrink-0">
              <div className="w-20 h-24 rounded-md bg-gradient-to-b from-ink-light to-ink
                              flex items-center justify-center text-4xl shadow-scroll">
                📜
              </div>
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <h3 className="font-title text-xl font-bold text-ink tracking-widest">
                  《{s.title || '未命名故事'}》
                </h3>
                {s.status === 'finished' ? (
                  <span className="px-2 py-0.5 text-[11px] rounded bg-bamboo/12 text-bamboo border border-bamboo/30 tracking-widest">
                    已完结
                  </span>
                ) : (
                  <span className="px-2 py-0.5 text-[11px] rounded bg-cinnabar/12 text-cinnabar border border-cinnabar/30 tracking-widest">
                    进行中
                  </span>
                )}
              </div>
              <div className="text-xs text-ink-light tracking-widest mb-3">
                来自《{s.novel_title}》 · {s.target_character} ↔ {s.user_persona_name}
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <Mini label="进度" value={`${s.current_chapter}/${s.total_chapters} 章`} />
                <Mini label="实力" value={s.user_power_level} />
                <Mini
                  label={`与${s.target_character}`}
                  value={String(s.relationship_meter[s.target_character] ?? 0)}
                />
                <Mini
                  label="更新"
                  value={new Date(s.updated_at).toLocaleDateString('zh-CN')}
                />
              </div>
            </div>

            <div className="flex md:flex-col gap-2 md:justify-center">
              <button
                onClick={() => nav(`/stories/${s.id}`)}
                className="btn-cinnabar py-2 text-sm whitespace-nowrap"
              >
                <FileEdit className="w-4 h-4" />
                {s.status === 'finished' ? '阅读' : '继续'}
              </button>
              <a
                href={storiesApi.exportUrl(s.id)}
                className="btn-ghost py-2 text-sm whitespace-nowrap"
                download
              >
                <Download className="w-4 h-4" /> 导出
              </a>
              <button
                onClick={() => {
                  if (confirm(`删除《${s.title}》?`)) remove.mutate(s.id)
                }}
                className="btn-ghost py-2 text-sm text-cinnabar/80"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="px-2 py-1 rounded bg-cream/70 border border-ink/10">
      <div className="text-[10px] text-ink-light tracking-widest">{label}</div>
      <div className="font-title text-ink truncate">{value}</div>
    </div>
  )
}
