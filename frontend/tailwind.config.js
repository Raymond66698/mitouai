/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ── 财运旺暖色表面层级 ──
        base: {
          0: '#FFFBF5',    // 最暖底色（奶油白）
          1: '#FFF8EE',    // 主背景（象牙白）
          2: '#FFFFFF',    // 卡片纯白
          3: '#FFF3E0',    // 悬浮高亮（暖金底）
          4: '#F0E6D3',    // 边框（暖奶油）
        },
        // ── 文字层级 ──
        ink: {
          primary: '#1A1A2E',    // 主文字（深藏青，非纯黑）
          secondary: '#6B5B4E',  // 辅助文字（暖灰棕）
          muted: '#A09080',      // 弱化文字
          inverse: '#FFFFFF',     // 反色白色
        },
        // ── 财运金主色调 ──
        primary: {
          50: '#FFF9ED',
          100: '#FEF0D0',
          200: '#FDE0A0',
          300: '#FBD06E',
          400: '#F9BE3C',
          500: '#E8A817',   // 主金色
          600: '#C8963E',   // 深金（CTA）
          700: '#A0762A',
          800: '#7A591E',
          900: '#5A3F14',
          950: '#3D2A0C',
        },
        // ── 财运红强调色 ──
        accent: {
          50: '#FFF5F5',
          100: '#FEE5E5',
          200: '#FECACA',
          300: '#FCA5A5',
          400: '#F87171',
          500: '#C41E3A',   // 中国红（重要提示/促销）
          600: '#A3152E',
          700: '#821024',
          800: '#610C1A',
          900: '#450A14',
        },
        // ── 涨跌色（中国习惯：红涨绿跌） ──
        up: {
          light: '#FEE2E2',
          DEFAULT: '#DC2626',
          deep: '#B91C1C',
        },
        down: {
          light: '#D1FAE5',
          DEFAULT: '#059669',
          deep: '#047857',
        },
        success: '#059669',
        danger: '#DC2626',
        warning: '#E8A817',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
        display: ['Inter', 'PingFang SC', 'Microsoft YaHei', 'sans-serif'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.875rem' }],
        'display-xl': ['3.5rem', { lineHeight: '1.1', letterSpacing: '-0.02em' }],
        'display-lg': ['2.75rem', { lineHeight: '1.15', letterSpacing: '-0.015em' }],
        'display-md': ['2rem', { lineHeight: '1.2', letterSpacing: '-0.01em' }],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.25rem',
        '4xl': '1.5rem',
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgba(139, 115, 85, 0.08), 0 1px 2px -1px rgba(139, 115, 85, 0.06)',
        'card-hover': '0 8px 24px 0 rgba(139, 115, 85, 0.12), 0 2px 8px -2px rgba(200, 150, 62, 0.08)',
        'glow-gold': '0 0 30px rgba(200, 150, 62, 0.2)',
        'glow-red': '0 0 30px rgba(196, 30, 58, 0.15)',
        'card-gold': '0 2px 12px 0 rgba(200, 150, 62, 0.1), 0 1px 3px 0 rgba(139, 115, 85, 0.08)',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'hero-warm': 'radial-gradient(ellipse at 50% 0%, rgba(232, 168, 23, 0.12) 0%, transparent 50%), radial-gradient(ellipse at 80% 20%, rgba(196, 30, 58, 0.06) 0%, transparent 40%)',
        'hero-gold': 'linear-gradient(135deg, #FFF8EE 0%, #FFF3E0 30%, #FFFDF5 60%, #FEF0D0 100%)',
        'card-gold-border': 'linear-gradient(135deg, #C8963E 0%, #F9BE3C 50%, #C8963E 100%)',
        'btn-gold': 'linear-gradient(135deg, #C8963E 0%, #E8A817 50%, #C8963E 100%)',
        'btn-red': 'linear-gradient(135deg, #A3152E 0%, #C41E3A 100%)',
        'stat-glow': 'radial-gradient(ellipse at center, rgba(232, 168, 23, 0.08) 0%, transparent 70%)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 2s ease-in-out infinite',
        'float': 'float 3s ease-in-out infinite',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        },
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(200, 150, 62, 0.15)' },
          '50%': { boxShadow: '0 0 40px rgba(200, 150, 62, 0.3)' },
        },
      },
    },
  },
  plugins: [],
}
