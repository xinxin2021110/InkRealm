/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // 墨韵古风主题色
        rice: '#F5F0E6',           // 宣纸白 — 页面底色
        cream: '#FAF6F0',          // 米白 — 卡片底色
        ink: '#3D2914',            // 墨色 — 主要文字
        'ink-light': '#8B4513',    // 浅墨 — 次要文字
        cinnabar: '#CD5C5C',       // 朱砂 — 强调
        'cinnabar-deep': '#B0413E',
        gold: '#D4AF37',           // 金箔
        bamboo: '#2F4F4F',         // 竹青
        lotus: '#E8D4C4',          // 藕粉 — 用户消息底
        smoke: '#A9A9A9',
        scroll: '#EFE3CC',         // 卷轴底色
      },
      fontFamily: {
        title: ['"Noto Serif SC"', 'serif'],
        body: ['"Noto Serif SC"', '"Source Han Serif"', 'serif'],
        kai: ['"Ma Shan Zheng"', '"KaiTi"', 'cursive'],
        sans: ['"Noto Sans SC"', 'sans-serif'],
      },
      backgroundImage: {
        // 宣纸纹理 — 用 SVG noise 模拟
        'rice-paper':
          "radial-gradient(ellipse at center, rgba(245,240,230,1) 0%, rgba(238,228,210,1) 100%)",
        'ink-wash':
          "linear-gradient(180deg, rgba(61,41,20,0) 0%, rgba(61,41,20,0.08) 50%, rgba(61,41,20,0) 100%)",
      },
      boxShadow: {
        scroll: '0 4px 24px -4px rgba(61,41,20,0.18)',
        'scroll-hover': '0 8px 32px -4px rgba(61,41,20,0.32)',
        seal: '0 2px 0 rgba(176, 65, 62, 0.6)',
      },
      animation: {
        'fade-in': 'fadeIn 0.6s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        ink: 'inkSpread 1.4s ease-out infinite',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: 0 }, '100%': { opacity: 1 } },
        slideUp: {
          '0%': { opacity: 0, transform: 'translateY(16px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
        inkSpread: {
          '0%, 100%': { transform: 'scale(0.85)', opacity: 0.4 },
          '50%': { transform: 'scale(1.15)', opacity: 1 },
        },
      },
    },
  },
  plugins: [],
}
