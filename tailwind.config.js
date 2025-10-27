/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './myApp/templates/**/*.html',
    './myApp/static/**/*.js',
    './static/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        // Your custom color palette
        'primary-purple': '#6D28D9',
        'primary-purple-hover': '#5B21B6',
        'deep-navy': '#0B0E14',
        'electric-violet': '#8B5CF6',
        'aqua-edge': '#18AFAB',
        'surface-slate': '#101323',
        'success-emerald': '#10B981',
        'warning-amber': '#F59E0B',
        'destructive-rose': '#EF4444',
      },
      fontFamily: {
        'inter': ['Inter', 'sans-serif'],
      },
      backdropBlur: {
        'xs': '2px',
      },
      animation: {
        'fade-in-up': 'fadeInUp 0.6s ease-out',
        'slide-in-right': 'slideInRight 0.4s ease-out',
        'pulse': 'pulse 2s infinite',
      },
      keyframes: {
        fadeInUp: {
          '0%': {
            opacity: '0',
            transform: 'translateY(20px)',
          },
          '100%': {
            opacity: '1',
            transform: 'translateY(0)',
          },
        },
        slideInRight: {
          '0%': {
            opacity: '0',
            transform: 'translateX(20px)',
          },
          '100%': {
            opacity: '1',
            transform: 'translateX(0)',
          },
        },
      },
    },
  },
  plugins: [],
}
