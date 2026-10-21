import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: [
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        /*
          Fon va yuzalar. Sof qora emas, biroz ko'kish — ekranda yumshoqroq
          ko'rinadi va globus "kosmosda" turgandek taassurot beradi.
        */
        ink: {
          950: '#06070d',  // sahifa foni
          900: '#0a0c14',  // birinchi daraja yuza (kartochka)
          850: '#0f1119',  // ko'tarilgan yuza (hover)
          800: '#151824',  // ikkinchi daraja
          700: '#1f2331',  // chegara (kuchli)
          600: '#2b3042',  // chegara (yumshoq)
        },
        /*
          Matn darajalari. Toza oq ishlatilmaydi — u qora fonda "qichqiradi".
        */
        text: {
          primary: '#e9ebf2',
          secondary: '#9aa2b8',
          muted: '#636b83',
        },
        /*
          Yagona brend aksenti. Kamdan-kam, lekin qat'iy ishlatiladi:
          faol holat, jonli efir, choropleth shkalasi.
        */
        signal: {
          DEFAULT: '#ff2d55',
          bright: '#ff5276',
          dim: '#c41e3f',
          deep: '#5c0d1d',
        },
        // Xato va ogohlantirish uchun ALOHIDA rang: aks holda qizil bir vaqtda
        // ham brend, ham xato bo'lib, foydalanuvchini chalkashtiradi
        warn: '#ffb02e',
      },
      fontFamily: {
        // Sarlavhalar — texnik, lekin o'qishga qulay grotesk
        display: ['var(--font-display)', 'system-ui', 'sans-serif'],
        // Asosiy matn
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
        // FAQAT raqamlar, kodlar va o'lchovlar uchun
        mono: ['var(--font-mono)', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        // Yagona, o'lchovli soya to'plami — oldin har joyda turli xil
        // "glow" ishlatilib, interfeys g'ovlab ketgandi
        card: '0 1px 2px rgba(0,0,0,0.4), 0 8px 24px -12px rgba(0,0,0,0.8)',
        lifted: '0 2px 4px rgba(0,0,0,0.5), 0 16px 48px -16px rgba(0,0,0,0.9)',
        signal: '0 0 0 1px rgba(255,45,85,0.35), 0 8px 32px -8px rgba(255,45,85,0.45)',
      },
      animation: {
        'fade-up': 'fadeUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) both',
        'fade-in': 'fadeIn 0.3s ease-out both',
        'live-pulse': 'livePulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeUp: {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        livePulse: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.35' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
