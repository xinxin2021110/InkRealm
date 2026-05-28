import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { MessageCircle, PenLine, Library, Sparkles } from 'lucide-react'

const HIGHLIGHTS = [
  {
    icon: '📜',
    title: '原著魂魄',
    desc: '检索 100+ 真实语录,角色"记得"小说里的每一段往事',
  },
  {
    icon: '🪶',
    title: '与卿同笔',
    desc: '化身为故事里的一员,与林动等主角共谱崭新章回',
  },
  {
    icon: '🎴',
    title: '玄机自取',
    desc: '4 维人设 × 4 路抉择,你的每一步都在影响剧情走向',
  },
]

export default function Home() {
  return (
    <div className="relative">
      <section className="max-w-5xl mx-auto px-6 pt-20 pb-12 text-center">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full
                          bg-cinnabar/8 border border-cinnabar/20 mb-6">
            <Sparkles className="w-3.5 h-3.5 text-cinnabar" />
            <span className="text-xs font-title text-cinnabar tracking-widest">
              一笔写就 · 古今同游
            </span>
          </div>

          <h1 className="font-title text-6xl md:text-7xl font-black text-ink leading-tight tracking-wider">
            墨韵书境
          </h1>
          <div className="mt-3 text-base md:text-lg font-kai text-ink-light tracking-widest">
            穿越书页,与角色共绘传奇
          </div>

          <p className="mt-8 max-w-2xl mx-auto text-ink-light/90 leading-loose">
            邀请你与心中那位少年并肩 —— 听他在族比前的低语,与他在天元境的星空下并肩而立。
            <br />
            点墨为引,落笔成卷,每一句话、每一个抉择,都是只属于你们二人的传奇。
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/library" className="btn-primary text-base px-8 py-3">
              <MessageCircle className="w-5 h-5" />
              开始一段对谈
            </Link>
            <Link to="/library" className="btn-cinnabar text-base px-8 py-3">
              <PenLine className="w-5 h-5" />
              共谱新的传奇
            </Link>
          </div>

          <Link
            to="/library"
            className="inline-flex items-center gap-1.5 mt-6 text-sm text-ink-light hover:text-ink transition"
          >
            <Library className="w-4 h-4" />
            浏览所有可玩角色 →
          </Link>
        </motion.div>
      </section>

      <section className="max-w-6xl mx-auto px-6 pb-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {HIGHLIGHTS.map((h, i) => (
            <motion.div
              key={h.title}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.15 * i }}
              className="scroll-card p-7 text-center"
            >
              <div className="text-5xl mb-3">{h.icon}</div>
              <div className="font-title text-xl font-bold text-ink mb-2 tracking-widest">
                {h.title}
              </div>
              <div className="text-sm text-ink-light leading-relaxed">{h.desc}</div>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="max-w-4xl mx-auto px-6 pb-20">
        <div className="ancient-page rounded-md p-10 text-center">
          <div className="font-kai text-2xl text-ink mb-3 tracking-widest">
            "书卷多情似故人,晨昏忧乐每相亲"
          </div>
          <div className="text-sm text-ink-light tracking-widest">— 于谦《观书》</div>
        </div>
      </section>
    </div>
  )
}
