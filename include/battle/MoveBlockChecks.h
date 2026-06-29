#pragma once

class Pokemon;
class Move;
class Side;
struct RuntimeMoveState;

namespace MoveBlockChecks {

bool isMoveDisabledForActor(const RuntimeMoveState& state, Pokemon* actor, const Move& move);
bool isMoveBlockedByTaunt(const RuntimeMoveState& state, Pokemon* actor, const Move& move);
bool isMoveBlockedByTorment(const RuntimeMoveState& state, Pokemon* actor, const Move& move);
bool isMoveBlockedByHealBlock(const RuntimeMoveState& state, Pokemon* actor, const Move& move);
bool isItemUsageBlockedByEmbargo(const RuntimeMoveState& state, Pokemon* actor);
bool isMoveBlockedByQuickGuard(const RuntimeMoveState& state, Pokemon* attacker, Pokemon* defender,
                               const Move& move, const Side& sideA, const Side& sideB);
bool isMoveBlockedByArmorTail(Pokemon* attacker, Pokemon* defender, const Move& move,
                              const Side& sideA, const Side& sideB);
bool isMoveBlockedByWideGuard(const RuntimeMoveState& state, Pokemon* attacker, Pokemon* defender,
                              const Move& move, const Side& sideA, const Side& sideB);
bool canBeForcedToSwitch(const RuntimeMoveState& state, Pokemon* defender,
                         const Side& sideA, const Side& sideB);
bool isMoveBlockedByImprison(const RuntimeMoveState& state, Pokemon* actor, const Move& move,
                             const Side& sideA, const Side& sideB);

void applyDisableToTarget(RuntimeMoveState& state, Pokemon* target);
void clearVolatileSwitchState(Pokemon* pokemon);

} // namespace MoveBlockChecks
