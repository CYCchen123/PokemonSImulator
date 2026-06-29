// Pokemon type name mappings (value -> { name, label, color })
export const TYPES = {
  0:  { name: 'Normal', label: '一般', color: '#A8A878' },
  1:  { name: 'Fire', label: '火', color: '#F08030' },
  2:  { name: 'Water', label: '水', color: '#6890F0' },
  3:  { name: 'Electric', label: '电', color: '#F8D030' },
  4:  { name: 'Grass', label: '草', color: '#78C850' },
  5:  { name: 'Ice', label: '冰', color: '#98D8D8' },
  6:  { name: 'Fighting', label: '格斗', color: '#C03028' },
  7:  { name: 'Poison', label: '毒', color: '#A040A0' },
  8:  { name: 'Ground', label: '地面', color: '#E0C068' },
  9:  { name: 'Flying', label: '飞行', color: '#A890F0' },
  10: { name: 'Psychic', label: '超能力', color: '#F85888' },
  11: { name: 'Bug', label: '虫', color: '#A8B820' },
  12: { name: 'Rock', label: '岩石', color: '#B8A038' },
  13: { name: 'Ghost', label: '幽灵', color: '#705898' },
  14: { name: 'Dragon', label: '龙', color: '#7038F8' },
  15: { name: 'Dark', label: '恶', color: '#705848' },
  16: { name: 'Steel', label: '钢', color: '#B8B8D0' },
  17: { name: 'Fairy', label: '妖精', color: '#EE99AC' },
}

export const STATUS_MAP = {
  0: { name: 'None', label: '无' },
  1: { name: 'Burn', label: '灼伤', icon: '🔥' },
  2: { name: 'Freeze', label: '冰冻', icon: '❄️' },
  3: { name: 'Paralysis', label: '麻痹', icon: '⚡' },
  4: { name: 'Poison', label: '中毒', icon: '☠️' },
  5: { name: 'Sleep', label: '睡眠', icon: '💤' },
  6: { name: 'Flinch', label: '畏缩', icon: '😨' },
  7: { name: 'ToxicPoison', label: '剧毒', icon: '💀' },
  8: { name: 'Confusion', label: '混乱', icon: '😵' },
}

export const WEATHER_MAP = {
  0: { name: 'Clear', label: '无天气' },
  1: { name: 'Rain', label: '雨天', icon: '🌧️' },
  2: { name: 'Sun', label: '晴天', icon: '☀️' },
  3: { name: 'Sandstorm', label: '沙暴', icon: '🏜️' },
  4: { name: 'Hail', label: '冰雹', icon: '🌨️' },
  5: { name: 'Snow', label: '雪天', icon: '❄️' },
}

export const FIELD_MAP = {
  0: { name: 'None', label: '无' },
  1: { name: 'Psychic', label: '精神场地' },
  2: { name: 'Electric', label: '电气场地' },
  3: { name: 'Grassy', label: '青草场地' },
  4: { name: 'Misty', label: '薄雾场地' },
  5: { name: 'TrickRoom', label: '戏法空间' },
}

export const CATEGORY_MAP = {
  0: { name: 'Physical', label: '物理', icon: '💥' },
  1: { name: 'Special', label: '特殊', icon: '✨' },
  2: { name: 'Status', label: '变化', icon: '🔄' },
}

export const STAT_NAMES = ['HP', '攻击', '防御', '特攻', '特防', '速度', '命中', '闪避']

export function getTypeInfo(id) { return TYPES[id] || null }
export function getStatusInfo(id) { return STATUS_MAP[id] || { name: 'Unknown', label: '未知' } }
export function getWeatherInfo(id) { return WEATHER_MAP[id] || { name: 'Clear', label: '无天气' } }
export function getFieldInfo(id) { return FIELD_MAP[id] || { name: 'None', label: '无' } }
