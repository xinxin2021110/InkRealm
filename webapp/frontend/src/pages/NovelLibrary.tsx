import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Search, Plus, BookOpen } from 'lucide-react'
import { novelsApi } from '../api/novels'
import LoadingScroll from '../components/LoadingScroll'
import ErrorView from '../components/ErrorView'
import PageTitle from '../components/PageTitle'

export default function NovelLibrary() {
  const [keyword, setKeyword] = useState('')

  const { data: novels = [], isLoading, error, refetch } = useQuery({
    queryKey: ['novels'],
    queryFn: novelsApi.list,
  })

  const filtered = useMemo(() => {
    const k = keyword.trim()
    if (!k) return novels
    return novels.filter(
      (n) =>
        n.title.includes(k) ||
        (n.author || '').includes(k) ||
        (n.description || '').includes(k),
    )
  }, [novels, keyword])

  return (
    <div className="max-w-7xl mx-auto px-6 py-10">
      <PageTitle
        title="小说中心"
        subtitle="选一部书,选一位心仪的角色,开启你们的故事"
        right={
          <Link to="/upload" className="btn-cinnabar">
            <Plus className="w-4 h-4" />
            上传小说
          </Link>
        }
      />

      <div className="relative mb-8 max-w-md">
        <Search className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-ink-light/60" />
        <input
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          className="bamboo-input pl-10"
          placeholder="搜索书名、作者…"
        />
      </div>

      {isLoading && <LoadingScroll text="正在翻阅书架…" />}
      {error && <ErrorView message={(error as Error).message} onRetry={() => refetch()} />}

      {!isLoading && filtered.length === 0 && (
        <div className="text-center py-20">
          <BookOpen className="w-12 h-12 mx-auto text-ink-light/40 mb-3" />
          <div className="text-ink-light">书架空空,先去【上传小说】添加一部吧</div>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {filtered.map((n, i) => (
          <motion.div
            key={n.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.05 * i }}
          >
            <Link
              to={`/novels/${n.id}`}
              className="scroll-card block p-6 h-full group"
            >
              <div className="flex items-start gap-4 mb-3">
                <div className="w-16 h-20 flex-shrink-0 rounded-md bg-gradient-to-b from-ink-light to-ink
                                flex items-center justify-center text-3xl shadow-scroll group-hover:shadow-scroll-hover transition">
                  <span className="drop-shadow">{n.cover_emoji}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-title text-xl font-bold text-ink truncate tracking-wider">
                    《{n.title}》
                  </div>
                  <div className="text-xs text-ink-light mt-1 tracking-widest">
                    {n.author || '佚名'}
                  </div>
                  <div className="mt-2 inline-block px-2 py-0.5 text-[11px] rounded-sm
                                  bg-cinnabar/10 text-cinnabar border border-cinnabar/30 tracking-wider">
                    {n.characters_count} 位角色
                  </div>
                </div>
              </div>
              <div className="text-sm text-ink-light/85 leading-relaxed line-clamp-3 mt-2">
                {n.description || '——'}
              </div>
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
