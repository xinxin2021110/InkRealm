import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { MessageCircle, PenLine, Library, Upload } from 'lucide-react'
import InkLogo from './InkLogo'

const NAV = [
  { to: '/library', icon: Library, label: '小说中心' },
  { to: '/chat', icon: MessageCircle, label: '墨笺对谈' },
  { to: '/stories', icon: PenLine, label: '我的故事' },
  { to: '/upload', icon: Upload, label: '上传小说' },
]

export default function Layout() {
  const location = useLocation()
  const isHome = location.pathname === '/'

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-30 backdrop-blur-md bg-rice/85 border-b border-ink/10">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <InkLogo className="w-9 h-9" />
            <div>
              <div className="font-title text-xl font-bold text-ink tracking-widest leading-none">
                墨韵书境
              </div>
              <div className="text-[10px] text-ink-light tracking-[0.4em] mt-1">INK · REALM</div>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {NAV.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `relative px-4 py-2 rounded-md font-title text-sm tracking-wider transition-all
                  ${isActive
                    ? 'text-cinnabar font-semibold'
                    : 'text-ink-light hover:text-ink'
                  }`
                }
              >
                {({ isActive }) => (
                  <span className="inline-flex items-center gap-1.5">
                    <Icon className="w-4 h-4" />
                    {label}
                    {isActive && (
                      <motion.span
                        layoutId="nav-underline"
                        className="absolute -bottom-0.5 left-3 right-3 h-[2px] bg-cinnabar rounded-full"
                      />
                    )}
                  </span>
                )}
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="gold-divider" />
      </header>

      <main className={`flex-1 ${isHome ? '' : 'pt-2'}`}>
        <Outlet />
      </main>

      <footer className="mt-12 py-6 border-t border-ink/10 text-center text-xs text-ink-light/70 font-title tracking-widest">
        墨韵书境 · 与古今笔下角色,共谱传奇 · v1.0
      </footer>
    </div>
  )
}
