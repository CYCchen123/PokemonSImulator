/**
 * Format HP as "current / max (percentage%)"
 */
export function formatHP(current, max) {
  const pct = max > 0 ? Math.round((current / max) * 100) : 0
  return { text: `${current} / ${max}`, pct }
}

/**
 * Get HP bar color based on percentage
 */
export function hpBarColor(pct) {
  if (pct > 50) return 'bg-green-500'
  if (pct > 20) return 'bg-yellow-500'
  return 'bg-red-500'
}

/**
 * Format stat stage (e.g., +2, -1, 0)
 */
export function formatStatStage(stage) {
  if (stage > 0) return `+${stage}`
  return `${stage}`
}

/**
 * Format stat stage CSS class
 */
export function statStageClass(stage) {
  if (stage > 0) return 'text-green-400'
  if (stage < 0) return 'text-red-400'
  return 'text-gray-400'
}

/**
 * Format date string
 */
export function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

/**
 * Format win rate
 */
export function formatWinRate(wins, total) {
  if (!total) return '0%'
  return `${Math.round((wins / total) * 100)}%`
}
