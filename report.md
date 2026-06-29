# 🌸 Code Quality Analysis Report 🌸

## 📑 Table of Contents

- [Issue Score](#overall-score)
- [Metrics Details](#metrics-details)
- [Problem Files Ranking](#problem-files)
- [Diagnosis](#conclusion)

![Score](https://img.shields.io/badge/Score-61%25-green)

## Issue Score {#overall-score}

| Metrics Summary | Score |
|------|-------|
| **Issue Score** | **61.21/100** |
| Quality Level | 😷 Code reeks, mask up |

> A bit smelly, but not lethal—just hold your nose and keep going

### 📊 Statistics

| Metric | Value |
|--------|-------|
| Total Files | 61 |
| Skipped | 213 |
| Time | 3357ms |

## Metrics Details {#metrics-details}

| Metrics Summary | Score | Status |
|:-----|------:|:------:|
| Cyclomatic Complexity | 15.85% | ✓✓ |
| Cognitive Complexity | 14.12% | ✓✓ |
| Nesting Depth | 10.90% | ✓✓ |
| Function Length | 8.25% | ✓✓ |
| File Length | 10.89% | ✓✓ |
| Parameter Count | 7.02% | ✓✓ |
| Code Duplication | 6.30% | ✓✓ |
| Structure Analysis | 6.19% | ✓✓ |
| Error Handling | 13.91% | ✓✓ |
| Comment Ratio | 69.30% | ⚠ |
| Naming Convention | 26.23% | ✓ |

## Problem Files Ranking {#problem-files}

### 1. src/battle/Battle.cpp

**Issue Score: 53.08**

**Issues**: 🔄 Complexity Issues: 22, ⚠️ Other Issues: 5, 📋 Duplication Issues: 6, 🏗️ Structure Issues: 9, 📝 Comment Issues: 1, 🏷️ Naming Issues: 10

- 🔄 `triggerToString()` L20: Complexity: 13
- 🔄 `itemTriggerToString()` L37: Complexity: 14
- 🔄 `applyCudChewBerryEffect()` L102: Complexity: 17
- 🔄 `resolveNextAction()` L1315: Complexity: 72
- 🔄 `calculateDamage()` L1856: Complexity: 62
- 🔍 ...and 45 more issues too smelly to list

### 2. src/tests/ItemTestRunner.cpp

**Issue Score: 50.89**

**Issues**: 🔄 Complexity Issues: 7, ⚠️ Other Issues: 6, 🏗️ Structure Issues: 3, 📝 Comment Issues: 1

- 🔄 `toItemSlug()` L15: Complexity: 107
- 🔄 `runSingleItemTestWithContext()` L151: Complexity: 145
- 🔄 `runAllItemTests()` L880: Complexity: 15
- 🔄 `toItemSlug()` L15: Cognitive Complexity: 109
- 🔄 `runSingleItemTestWithContext()` L151: Cognitive Complexity: 151
- 🔍 ...and 10 more issues too smelly to list

### 3. src/battle/Moves.cpp

**Issue Score: 49.24**

**Issues**: 🔄 Complexity Issues: 4, ⚠️ Other Issues: 4, 🏗️ Structure Issues: 3, 📝 Comment Issues: 1

- 🔄 `initializeCoreMoveRules()` L319: Complexity: 304
- 🔄 `initializeCoreMoveRules()` L319: Cognitive Complexity: 312
- 🔄 `applyProtectionContactPunish()` L289: Nesting Depth: 4
- 🔄 `initializeCoreMoveRules()` L319: Nesting Depth: 4
- 📏 `initializeCoreMoveRules()` L319: 1995 Size
- 🔍 ...and 5 more issues too smelly to list

### 4. tests/battle_data_test.cpp

**Issue Score: 48.24**

**Issues**: 🔄 Complexity Issues: 6, ⚠️ Other Issues: 6, 📋 Duplication Issues: 13, 🏗️ Structure Issues: 10, ❌ Error Handling Issues: 8, 📝 Comment Issues: 1

- 🔄 `countSpecialEventsByReason()` L81: Complexity: 14
- 🔄 `TEST()` L6015: Complexity: 11
- 🔄 `countSpecialEventsByReason()` L81: Cognitive Complexity: 18
- 🔄 `TEST()` L5669: Cognitive Complexity: 16
- 🔄 `TEST()` L6015: Cognitive Complexity: 21
- 🔍 ...and 37 more issues too smelly to list

### 5. src/battle/Abilities.cpp

**Issue Score: 45.05**

**Issues**: 🔄 Complexity Issues: 8, ⚠️ Other Issues: 5, 🏗️ Structure Issues: 3

- 🔄 `getAbilityName()` L130: Complexity: 303
- 🔄 `getAbilityTypeByName()` L437: Complexity: 305
- 🔄 `abilityWeatherSpeedMultiplier()` L1932: Complexity: 11
- 🔄 `initializeCoreAbilities()` L1950: Complexity: 45
- 🔄 `getAbilityName()` L130: Cognitive Complexity: 305
- 🔍 ...and 10 more issues too smelly to list

### 6. src/IO/BattleToJson.cpp

**Issue Score: 43.14**

**Issues**: 🔄 Complexity Issues: 13, ⚠️ Other Issues: 1, 🏗️ Structure Issues: 5, ❌ Error Handling Issues: 1, 📝 Comment Issues: 1

- 🔄 `buildDescription()` L82: Complexity: 26
- 🔄 `buildIndexedTimeline()` L161: Complexity: 13
- 🔄 `typeToString()` L300: Complexity: 20
- 🔄 `natureToString()` L336: Complexity: 27
- 🔄 `abilityTypeToString()` L368: Complexity: 80
- 🔍 ...and 14 more issues too smelly to list

### 7. src/IO/AbilityData.cpp

**Issue Score: 42.07**

**Issues**: 🔄 Complexity Issues: 9, ⚠️ Other Issues: 3, 🏗️ Structure Issues: 3, ❌ Error Handling Issues: 3, 📝 Comment Issues: 1

- 🔄 `fallbackAbilityDataById()` L80: Complexity: 85
- 🔄 `upsertAbilityEntry()` L327: Complexity: 78
- 🔄 `collectReferencedAbilityIds()` L441: Complexity: 15
- 🔄 `getAbilityData()` L557: Complexity: 74
- 🔄 `fallbackAbilityDataById()` L80: Cognitive Complexity: 87
- 🔍 ...and 11 more issues too smelly to list

### 8. src/IO/BattleSession.cpp

**Issue Score: 41.92**

**Issues**: 🔄 Complexity Issues: 7, ⚠️ Other Issues: 3, 📋 Duplication Issues: 1, 🏗️ Structure Issues: 4, ❌ Error Handling Issues: 2, 📝 Comment Issues: 1, 🏷️ Naming Issues: 2

- 🔄 `processTurn()` L370: Complexity: 60
- 🔄 `createFromJson()` L186: Cognitive Complexity: 18
- 🔄 `createDeferred()` L247: Cognitive Complexity: 18
- 🔄 `processTurn()` L370: Cognitive Complexity: 72
- 🔄 `createFromJson()` L186: Nesting Depth: 4
- 🔍 ...and 12 more issues too smelly to list

### 9. src/battle/Items.cpp

**Issue Score: 40.89**

**Issues**: 🔄 Complexity Issues: 7, ⚠️ Other Issues: 4, 🏗️ Structure Issues: 2, 📝 Comment Issues: 1

- 🔄 `getItemName()` L26: Complexity: 168
- 🔄 `initializeCoreItems()` L198: Complexity: 106
- 🔄 `isBerry()` L1010: Complexity: 40
- 🔄 `getItemName()` L26: Cognitive Complexity: 170
- 🔄 `initializeCoreItems()` L198: Cognitive Complexity: 116
- 🔍 ...and 6 more issues too smelly to list

### 10. src/IO/MoveData.cpp

**Issue Score: 37.58**

**Issues**: 🔄 Complexity Issues: 16, ⚠️ Other Issues: 2, 📋 Duplication Issues: 3, 🏗️ Structure Issues: 4, ❌ Error Handling Issues: 3, 📝 Comment Issues: 1

- 🔄 `parseType()` L98: Complexity: 18
- 🔄 `parseEffect()` L127: Complexity: 18
- 🔄 `effectToString()` L159: Complexity: 19
- 🔄 `parseMoveEntry()` L225: Complexity: 19
- 🔄 `moveDataFromPokeAPI()` L334: Complexity: 16
- 🔍 ...and 21 more issues too smelly to list

## Diagnosis {#conclusion}

🌸 **Code reeks, mask up** - Code is starting to stink, approach with caution and a mask

👍 Keep going, you're the clean freak of the coding world, a true code hygiene champion

---

*Generated by [fuck-u-code](https://github.com/Done-0/fuck-u-code)*