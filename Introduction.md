# PokemonSimulator — 前端对接文档

## 项目概述

PokemonSimulator 是一个 **C++17 后端宝可梦第九世代单打对战模拟器**（不含太晶化），以 [Pokemon Showdown](https://github.com/smogon/pokemon-showdown) 的对战逻辑为蓝本实现。

**通信方式：** 前后端通过 `cache/` 目录下的 JSON 文件进行数据交换，无需网络协议或长连接。

---

## 功能覆盖

| 系统 | 覆盖情况 |
|------|----------|
| 招式 | 277/277 变化招式已全部实现 |
| 特性 | ~246 个对战特性已实现（剩余 Tera/Conquest 类型不适用于 Gen9 单打） |
| 道具 | 145 个对战道具已实现（含全部竞争性对战道具，冻结不再扩展） |
| 天气 | 晴天、雨天、沙暴、冰雹、雪天、无天气 |
| 场地 | 精神场地、电气场地、青草场地、薄雾场地、戏法空间、魔法空间、奇妙空间 |
| 状态 | 灼伤、麻痹、中毒、剧毒、睡眠、冰冻、畏缩、混乱 |
| 场地效果 | 隐形岩、撒菱、毒菱、光墙、反射壁、神秘守护、顺风等 |
| 对战流程 | 出手顺序判定、伤害计算、属性相克、会心一击、特性/道具触发、换人逻辑 |

---

## 通信协议

### 模式 A: 批量处理 (`--run-cache-input`)

前端将所有输入写入 `cache/input/`，模拟器一次性运行全部回合，输出到 `cache/output/`。

### 模式 B: 守护进程 (`--daemon`)

模拟器作为守护进程启动，每 500ms 轮询 `cache/input/`，检测到新回合文件即处理并输出结果。

### 输入文件

**队伍定义 (side_a.json / side_b.json):**

```json
{
  "pokemon": [
    {
      "speciesID": 25,
      "level": 50,
      "ability": 9,
      "nature": 3,
      "evs": { "hp": 0, "attack": 0, "defense": 0, "specialAttack": 252, "specialDefense": 0, "speed": 252 },
      "ivs": { "hp": 31, "attack": 31, "defense": 31, "specialAttack": 31, "specialDefense": 31, "speed": 31 },
      "moves": [85, 94, 109, 115]
    }
  ]
}
```

- `speciesID`: 宝可梦物种 ID（参见 `data/species.json`，如 25 = 皮卡丘）
- `ability`: 特性 ID（参见 `data/abilities.json`）
- `nature`: 性格枚举值（见下方 Nature 枚举表）
- `moves`: 招式 ID 数组，最多 4 个（参见 `data/moves.json`）

**回合动作 (turn_1_input_a.json / turn_1_input_b.json):**

```json
// 攻击
{ "type": "attack", "side": "a", "move_index": 0 }

// 换人
{ "type": "switch", "side": "a", "target_index": 2 }

// 跳过
{ "type": "pass", "side": "a" }
```

- `move_index`: 0–3，对应队伍定义中 moves 数组的下标
- `target_index`: 0–5，对应队伍中待换上的宝可梦序号

### 输出文件

每个回合输出 `cache/output/output_{turn}.json`，结构如下：

```json
{
  "turn": 1,
  "descriptions": ["描述文本1", "描述文本2"],
  "battle": {
    "turn": 1,
    "field": { "type": 0, "duration": 0 },
    "weather": { "type": 0, "duration": 0 },
    "sides": [
      {
        "side": 0,
        "name": "A",
        "active": 0,
        "count": 6,
        "sideEffects": {
          "lightScreen": 0, "mist": 0, "mudSport": 0,
          "reflect": 0, "safeguard": 0, "spikes": 0,
          "stealthRock": 0, "toxicSpikes": 0, "waterSport": 0
        },
        "pokemons": [
          {
            "slot": 0,
            "speciesId": 25,
            "hp": 150,
            "maxHp": 150,
            "fainted": false,
            "abilityId": 9,
            "itemId": 0,
            "types": [12, 18],
            "statStages": [0, 0, 0, 0, 0, 0, 0],
            "inBattleStatus": [
              { "id": 1, "duration": 2 }
            ],
            "moves": [
              { "slot": 0, "id": 85, "pp": 10, "maxPp": 10 }
            ]
          }
        ]
      }
    ]
  },
  "events": [
    {
      "timeline_index": 0,
      "turn_index": 1,
      "description": "皮卡丘上场了。",
      "details": {
        "pokemon": "Pikachu",
        "pokemon_ref": { "side_index": 0, "pokemon_index": 0 },
        "side": "A",
        "side_index": 0,
        "reason": "initial_send_out"
      }
    }
  ]
}
```

**关键说明：**
- `statStages` 数组顺序: `[攻击, 防御, 特攻, 特防, 速度, 命中率, 闪避率]`，范围 -6 ~ +6
- `types`: `[属性1, 属性2]`，如果第二属性为 18（Fairy）且宝可梦无第二属性，请用 `speciesId` 查 `data/species.json` 中的 `types` 字段确认
- `itemId: 0` 表示未携带道具
- `abilityId` / `itemId` 为 `data/` 下对应 JSON 文件中的 `id` 字段
- `speciesId` 为 `data/species.json` 中的 `id`

### 事件类型

每个事件的 `details` 包含 `*_ref` 引用字段，便于前端定位宝可梦：

| 事件类型 | details 字段 | 说明 |
|----------|-------------|------|
| `switch_in` | `pokemon`, `side`, `reason`, `pokemon_ref`, `side_index` | 宝可梦上场 |
| `switch` | `side`, `from`, `to`, `from_ref`, `to_ref`, `side_index` | 手动换人 |
| `ability_trigger` | `pokemon`, `ability`, `trigger`, `opponent`, `pokemon_ref`, `ability_index` | 特性触发 |
| `item_trigger` | `pokemon`, `item`, `trigger`, `opponent`, `pokemon_ref`, `item_index` | 道具触发 |
| `status_apply` | `pokemon`, `status`, `reason`, `status_index`, `pokemon_ref` | 状态附加 |
| `heal` | `pokemon`, `reason`, `from`, `to`, `delta`, `pokemon_ref` | HP 回复 |
| `stat_change` | `pokemon`, `stat`, `delta`, `move`, `pokemon_ref` | 能力变化 |
| `item_blocked` | `actor`, `item`, `reason`, `actor_ref`, `item_index` | 道具被阻止 |
| `item_replay` | `pokemon`, `reason`, `berry`, `from`, `to`, `pokemon_ref` | 道具再次生效 |

---

## 枚举定义

以下所有枚举在 JSON 中均以 **整数值** 表示。

### Type（属性）

| 值 | 名称 | 中文 |
|----|------|------|
| 0 | Normal | 一般 |
| 1 | Fire | 火 |
| 2 | Water | 水 |
| 3 | Electric | 电 |
| 4 | Grass | 草 |
| 5 | Ice | 冰 |
| 6 | Fighting | 格斗 |
| 7 | Poison | 毒 |
| 8 | Ground | 地面 |
| 9 | Flying | 飞行 |
| 10 | Psychic | 超能力 |
| 11 | Bug | 虫 |
| 12 | Rock | 岩石 |
| 13 | Ghost | 幽灵 |
| 14 | Dragon | 龙 |
| 15 | Dark | 恶 |
| 16 | Steel | 钢 |
| 17 | Fairy | 妖精 |

### Category（招式分类）

| 值 | 名称 | 中文 |
|----|------|------|
| 0 | Physical | 物理 |
| 1 | Special | 特殊 |
| 2 | Status | 变化 |

### WeatherType（天气）

| 值 | 名称 | 中文 |
|----|------|------|
| 0 | Clear | 无天气 |
| 1 | Rain | 雨天 |
| 2 | Sun | 晴天 |
| 3 | Sandstorm | 沙暴 |
| 4 | Hail | 冰雹 |
| 5 | Snow | 雪天 |

### FieldType（场地）

| 值 | 名称 | 中文 |
|----|------|------|
| 0 | None | 无场地 |
| 1 | Psychic | 精神场地 |
| 2 | Electric | 电气场地 |
| 3 | Grassy | 青草场地 |
| 4 | Misty | 薄雾场地 |
| 5 | TrickRoom | 戏法空间 |

### StatusType（状态）

| 值 | 名称 | 中文 |
|----|------|------|
| 0 | None | 无状态 |
| 1 | Burn | 灼伤 |
| 2 | Freeze | 冰冻 |
| 3 | Paralysis | 麻痹 |
| 4 | Poison | 中毒 |
| 5 | Sleep | 睡眠 |
| 6 | Flinch | 畏缩 |
| 7 | ToxicPoison | 剧毒 |
| 8 | Confusion | 混乱 |

### ActionType（动作类型）

| 值 | 名称 | 中文 |
|----|------|------|
| 0 | Attack | 攻击 |
| 1 | Switch | 换人 |
| 2 | UseItem | 使用道具 |
| 3 | Pass | 跳过 |

### StatIndex / StatChangeType（能力值 / 能力变化）

| 值 | StatIndex（能力） | StatChangeType（等级变化） | statStages 数组索引 |
|----|-------------------|---------------------------|---------------------|
| 0 | HP | — | — |
| 1 | Attack | Attack | `[0]` 攻击 |
| 2 | Defense | Defense | `[1]` 防御 |
| 3 | SpecialAttack | SpAttack | `[2]` 特攻 |
| 4 | SpecialDefense | SpDefense | `[3]` 特防 |
| 5 | Speed | Speed | `[4]` 速度 |
| 6 | — | Accuracy | `[5]` 命中率 |
| 7 | — | Evasion | `[6]` 闪避率 |

stat_stages 中每个值范围 [-6, 6]，0 为基准值。

### Nature（性格）

| 值 | 名称 | 加成 | 减益 |
|----|------|------|------|
| 0 | Hardy | — | — |
| 1 | Lonely | 攻击 | 防御 |
| 2 | Brave | 攻击 | 速度 |
| 3 | Adamant | 攻击 | 特攻 |
| 4 | Naughty | 攻击 | 特防 |
| 5 | Bold | 防御 | 攻击 |
| 6 | Docile | — | — |
| 7 | Relaxed | 防御 | 速度 |
| 8 | Impish | 防御 | 特攻 |
| 9 | Lax | 防御 | 特防 |
| 10 | Timid | 速度 | 攻击 |
| 11 | Hasty | 速度 | 防御 |
| 12 | Serious | — | — |
| 13 | Jolly | 速度 | 特攻 |
| 14 | Naive | 速度 | 特防 |
| 15 | Modest | 特攻 | 攻击 |
| 16 | Mild | 特攻 | 防御 |
| 17 | Quiet | 特攻 | 速度 |
| 18 | Bashful | — | — |
| 19 | Rash | 特攻 | 特防 |
| 20 | Calm | 特防 | 攻击 |
| 21 | Gentle | 特防 | 防御 |
| 22 | Sassy | 特防 | 速度 |
| 23 | Careful | 特防 | 特攻 |
| 24 | Quirky | — | — |

加成 = 1.1x，减益 = 0.9x

### Target（招式目标）

| 值 | 名称 | 说明 |
|----|------|------|
| 0 | Self | 自身 |
| 1 | Ally | 队友 |
| 2 | Opponent | 对手 |
| 3 | AllAllies | 所有队友 |
| 4 | AllOpponents | 所有对手 |
| 5 | All | 全场 |

### MoveEffect（招式效果类型）

| 值 | 名称 | 说明 |
|----|------|------|
| 0 | None | 无特殊效果 |
| 1 | Pursuit | 追击 |
| 2 | Encore | 再来一次 |
| 3 | Dig | 挖洞（两回合） |
| 4 | Round | 轮唱 |
| 5 | KnockOff | 拍落 |
| 6 | WeatherBall | 气象球 |
| 7 | Status | 状态变化 |
| 8 | StatChange | 能力变化 |
| 9 | Recoil | 反伤 |
| 10 | Drain | 吸血 |
| 11 | Flinch | 畏缩 |
| 12 | Paralyze | 麻痹 |
| 13 | Sleep | 睡眠 |
| 14 | Freeze | 冰冻 |
| 15 | Burn | 灼伤 |
| 16 | Poison | 中毒 |
| 17 | Confuse | 混乱 |
| 18 | LeechSeed | 寄生种子 |
| 19 | Reflect | 反射壁 |
| 20 | LightScreen | 光墙 |
| 21 | Safeguard | 守护 |
| 22 | Tailwind | 顺风 |
| 23 | StealthRock | 隐形岩 |
| 24 | Spikes | 撒菱 |
| 25 | ToxicSpikes | 毒菱 |

### FieldEffectType（场地持续效果类型）

| 值 | 名称 | 说明 |
|----|------|------|
| 0 | None | 无 |
| 1 | ToxicSpikes | 毒菱 |
| 2 | FireSpin | 火焰旋涡 |
| 3 | LeechSeed | 寄生种子 |
| 4 | StealthRock | 隐形岩 |

### SemiInvulnerableState（半无敌状态）

| 值 | 名称 | 说明 |
|----|------|------|
| 0 | None | 正常 |
| 1 | Underground | 挖洞中 |
| 2 | Airborne | 飞翔/弹跳中 |
| 3 | Underwater | 潜水中 |
| 4 | Phased | 潜灵奇袭中 |

### Trigger（特性触发时机）

| 值 | 名称 | 说明 |
|----|------|------|
| 0 | OnEntry | 上场时 |
| 1 | OnExit | 离场时 |
| 2 | OnTurnStart | 回合开始时 |
| 3 | OnTurnEnd | 回合结束时 |
| 4 | OnDamage | 受到伤害时 |
| 5 | OnDealDamage | 造成伤害时 |
| 6 | OnAttack | 攻击时 |
| 7 | OnFaint | 濒死时 |
| 8 | OnStatusInflicted | 施加状态时 |
| 9 | OnWeatherChange | 天气改变时 |
| 10 | OnTerrainChange | 场地改变时 |

### ItemTrigger（道具触发时机）

| 值 | 名称 | 说明 |
|----|------|------|
| 0 | OnEntry | 上场时 |
| 1 | OnTurnStart | 回合开始时 |
| 2 | OnTurnEnd | 回合结束时 |
| 3 | OnDamage | 受到伤害时 |
| 4 | OnDealDamage | 造成伤害时 |
| 5 | AfterDamage | 伤害结算后 |
| 6 | OnAttack | 攻击时 |
| 7 | OnFaint | 濒死时 |
| 8 | OnSwitchOut | 换下时 |
| 9 | OnStatChange | 能力变化时 |
| 10 | OnStatus | 状态变化时 |
| 11 | OnEat | 食用树果时 |
| 12 | AfterMoveMiss | 招式未命中后 |
| 13 | AfterSoundMove | 声音招式后 |

### EggGroup（蛋群）

| 值 | 名称 | | 值 | 名称 |
|----|------|-|----|------|
| 0 | None | | 8 | HumanLike |
| 1 | Monster | | 9 | Mineral |
| 2 | Water1 | | 10 | Amorphous |
| 3 | Water2 | | 11 | Ditto |
| 4 | Bug | | 12 | Dragon |
| 5 | Flying | | 13 | Undiscovered |
| 6 | Field | | | |
| 7 | Fairy | | | |

---

## 数据文件索引

`data/` 目录下包含所有宝可梦数据，前端应按需加载：

| 文件 | 记录数 | 用作 |
|------|--------|------|
| `data/species.json` | ~1300 | 宝可梦物种（ID → 名称、属性、种族值） |
| `data/moves.json` | ~900 | 招式（ID → 名称、属性、威力、命中率等） |
| `data/abilities.json` | ~370 | 特性（ID → 名称） |
| `data/items.json` | ~225 | 道具（ID → 名称） |

每个 JSON 文件结构为 `{ "moves": [...], "abilities": [...], ... }` 或 `{ "species": [...] }`，每个条目有 `id` 和 `name` 字段。

---

## 实战流程示例

一个完整的 3v3 对战流程（`scripts/full_battle_daemon.py` 提供了参考）：

1. 前端编写 `cache/input/side_a.json` 和 `side_b.json` 定义双方队伍
2. 确定胜率后编写每回合动作文件 `turn_1_input_a.json`, `turn_1_input_b.json` ……
3. 运行 `./build/PokemonSimulator --daemon` 启动守护进程
4. 守护进程检测到输入后处理回合，输出 `cache/output/output_1.json` ……
5. 当一方所有宝可梦濒死时，输出 `cache/output/game_over.json`
6. 前端逐回合读取 `output_N.json` 渲染对战动画
