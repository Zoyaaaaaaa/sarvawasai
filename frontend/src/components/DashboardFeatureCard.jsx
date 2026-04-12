import { ArrowUpRight } from 'lucide-react'

const variantStyles = {
  indigo: {
    card: 'from-[#1E3A8A]/95 to-[#334155]/90',
    icon: 'bg-white/15',
    description: 'text-blue-50/90',
    action: 'text-white/95',
  },
  plum: {
    card: 'from-[#581C87]/95 to-[#1E3A8A]/90',
    icon: 'bg-white/15',
    description: 'text-purple-50/90',
    action: 'text-white/95',
  },
  slate: {
    card: 'from-[#334155]/95 to-[#0F172A]/90',
    icon: 'bg-white/15',
    description: 'text-slate-100/90',
    action: 'text-white/95',
  },
  amber: {
    card: 'from-[#C2410C]/95 to-[#D97706]/90',
    icon: 'bg-white/15',
    description: 'text-orange-50/90',
    action: 'text-white/95',
  },
}

export default function DashboardFeatureCard({
  title,
  description,
  actionLabel,
  icon: Icon,
  onClick,
  variant = 'indigo',
  className = '',
}) {
  const styles = variantStyles[variant] || variantStyles.indigo

  return (
    <button
      type="button"
      onClick={onClick}
      className={`group relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br ${styles.card} p-8 text-left shadow-lg transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#581C87]/25 ${className}`}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.18),transparent_42%)] opacity-70 transition-opacity duration-300 group-hover:opacity-100" />
      <div className="relative flex h-full flex-col">
        <div className={`mb-4 flex h-12 w-12 items-center justify-center rounded-xl ${styles.icon} backdrop-blur-sm transition-transform duration-300 group-hover:scale-105`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
        <h3 className="mb-2 text-2xl font-semibold tracking-tight text-white">{title}</h3>
        <p className={`mb-5 max-w-md text-sm leading-6 ${styles.description}`}>
          {description}
        </p>
        <div className={`mt-auto flex items-center gap-2 text-sm font-semibold ${styles.action}`}>
          <span>{actionLabel}</span>
          <ArrowUpRight className="h-4 w-4 transition-transform duration-300 group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
        </div>
      </div>
    </button>
  )
}