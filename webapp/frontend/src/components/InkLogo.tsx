// 墨韵 logo — 印章风格的"墨"字图形 (用 SVG 自绘,避免外部图片)
export default function InkLogo({ className = 'w-10 h-10' }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 64 64"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <defs>
        <radialGradient id="seal-bg" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#CD5C5C" />
          <stop offset="100%" stopColor="#9F3A37" />
        </radialGradient>
      </defs>
      <rect
        x="4" y="4" width="56" height="56" rx="6"
        fill="url(#seal-bg)"
        stroke="#5C2E0B" strokeWidth="1.5"
      />
      {/* 内框 */}
      <rect
        x="9" y="9" width="46" height="46" rx="3"
        fill="none" stroke="#F5F0E6" strokeWidth="1.5" opacity="0.65"
      />
      {/* 墨字 */}
      <text
        x="50%" y="56%"
        textAnchor="middle"
        dominantBaseline="middle"
        fontFamily="'Noto Serif SC', 'Ma Shan Zheng', serif"
        fontSize="34"
        fontWeight="900"
        fill="#F5F0E6"
        style={{ letterSpacing: '0.05em' }}
      >
        墨
      </text>
    </svg>
  )
}
