#include "battle/MoveBlockChecks.h"
#include "battle/Battle.h"
#include "battle/Pokemon.h"
#include "battle/Side.h"
#include "battle/Moves.h"
#include "battle/Abilities.h"

namespace MoveBlockChecks {

static const Side* findSideFor(const Pokemon* pokemon, const Side& sideA, const Side& sideB) {
    if (sideA.getActivePokemon() == pokemon) return &sideA;
    if (sideB.getActivePokemon() == pokemon) return &sideB;
    for (Pokemon* member : sideA.getTeam()) {
        if (member == pokemon) return &sideA;
    }
    for (Pokemon* member : sideB.getTeam()) {
        if (member == pokemon) return &sideB;
    }
    return nullptr;
}

bool isMoveDisabledForActor(const RuntimeMoveState& state, Pokemon* actor, const Move& move) {
    if (!actor) return false;
    const auto it = state.disableState.find(actor);
    if (it == state.disableState.end() || it->second.lockedMoveName.empty()) return false;
    return normalizeMoveName(move.getName()) == normalizeMoveName(it->second.lockedMoveName);
}

bool isMoveBlockedByTaunt(const RuntimeMoveState& state, Pokemon* actor, const Move& move) {
    if (!actor || move.getCategory() != Category::Status) return false;
    const auto it = state.tauntState.find(actor);
    return it != state.tauntState.end() && it->second.remainingTurns > 0;
}

bool isMoveBlockedByTorment(const RuntimeMoveState& state, Pokemon* actor, const Move& move) {
    if (!actor) return false;
    const auto it = state.tormentState.find(actor);
    if (it == state.tormentState.end() || it->second.remainingTurns <= 0) return false;
    const auto lastMoveIt = state.lastUsedMoveName.find(actor);
    if (lastMoveIt == state.lastUsedMoveName.end() || lastMoveIt->second.empty()) return false;
    return normalizeMoveName(lastMoveIt->second) == normalizeMoveName(move.getName());
}

bool isMoveBlockedByHealBlock(const RuntimeMoveState& state, Pokemon* actor, const Move& move) {
    if (!actor) return false;
    const auto it = state.healBlockState.find(actor);
    if (it == state.healBlockState.end() || it->second.remainingTurns <= 0) return false;
    return isHealingMove(move);
}

bool isItemUsageBlockedByEmbargo(const RuntimeMoveState& state, Pokemon* actor) {
    if (!actor) return false;
    const auto it = state.embargoState.find(actor);
    return it != state.embargoState.end() && it->second.remainingTurns > 0;
}

bool isMoveBlockedByQuickGuard(const RuntimeMoveState& state, Pokemon* attacker, Pokemon* defender,
                               const Move& move, const Side& sideA, const Side& sideB) {
    if (!attacker || !defender) return false;
    if (move.getPriority() <= 0) return false;
    const Side* attackerSide = findSideFor(attacker, sideA, sideB);
    const Side* defenderSide = findSideFor(defender, sideA, sideB);
    if (!attackerSide || !defenderSide || attackerSide == defenderSide) return false;
    auto it = state.quickGuardActive.find(defenderSide);
    return it != state.quickGuardActive.end() && it->second;
}

bool isMoveBlockedByArmorTail(Pokemon* attacker, Pokemon* defender, const Move& move,
                              const Side& sideA, const Side& sideB) {
    if (!attacker || !defender) return false;
    if (move.getPriority() <= 0) return false;
    const Side* attackerSide = findSideFor(attacker, sideA, sideB);
    const Side* defenderSide = findSideFor(defender, sideA, sideB);
    if (!attackerSide || !defenderSide || attackerSide == defenderSide) return false;
    return abilityBlocksPriorityTargetedMoves(defender->getAbility());
}

bool isMoveBlockedByWideGuard(const RuntimeMoveState& state, Pokemon* attacker, Pokemon* defender,
                              const Move& move, const Side& sideA, const Side& sideB) {
    if (!attacker || !defender) return false;
    if (move.getTarget() != Target::AllOpponents && move.getTarget() != Target::All) return false;
    const Side* attackerSide = findSideFor(attacker, sideA, sideB);
    const Side* defenderSide = findSideFor(defender, sideA, sideB);
    if (!attackerSide || !defenderSide || attackerSide == defenderSide) return false;
    auto it = state.wideGuardActive.find(defenderSide);
    return it != state.wideGuardActive.end() && it->second;
}

bool canBeForcedToSwitch(const RuntimeMoveState& state, Pokemon* defender,
                         const Side& sideA, const Side& sideB) {
    if (!defender || defender->getSubstituteHP() > 0) return false;
    const auto ingrainIt = state.ingrainActive.find(defender);
    if (ingrainIt != state.ingrainActive.end() && ingrainIt->second) return false;
    const auto trappedIt = state.trappedBySource.find(defender);
    if (trappedIt != state.trappedBySource.end()) {
        Pokemon* trappingSource = trappedIt->second;
        const Side* defenderSide = findSideFor(defender, sideA, sideB);
        const Side* sourceSide = findSideFor(trappingSource, sideA, sideB);
        const bool stillTrapped = trappingSource && !trappingSource->isFainted()
            && defenderSide && sourceSide && defenderSide != sourceSide;
        if (stillTrapped) return false;
    }
    return true;
}

bool isMoveBlockedByImprison(const RuntimeMoveState& state, Pokemon* actor, const Move& move,
                             const Side& sideA, const Side& sideB) {
    if (!actor) return false;
    const Side* actorSide = findSideFor(actor, sideA, sideB);
    if (!actorSide) return false;
    const Side& opponentSide = (actorSide == &sideA) ? sideB : sideA;
    Pokemon* opponentActive = opponentSide.getActivePokemon();
    if (!opponentActive || opponentActive->isFainted()) return false;
    const auto imprisonIt = state.imprisonActive.find(opponentActive);
    if (imprisonIt == state.imprisonActive.end() || !imprisonIt->second) return false;
    const std::string selectedMoveName = normalizeMoveName(move.getName());
    for (const Move& opponentMove : opponentActive->getMoves()) {
        if (normalizeMoveName(opponentMove.getName()) == selectedMoveName) return true;
    }
    return false;
}

void applyDisableToTarget(RuntimeMoveState& state, Pokemon* target) {
    if (!target) return;
    const auto it = state.lastUsedMoveName.find(target);
    if (it == state.lastUsedMoveName.end() || it->second.empty()) return;
    state.disableState[target] = DisableState{it->second, 4};
}

void clearVolatileSwitchState(Pokemon* pokemon) {
    if (!pokemon) return;
    pokemon->clearSubstitute();
    pokemon->clearLeechSeedSource();
    if (pokemon->getAccuracyStage() != 0) {
        pokemon->changeAccuracyStage(-pokemon->getAccuracyStage());
    }
    if (pokemon->getEvasionStage() != 0) {
        pokemon->changeEvasionStage(-pokemon->getEvasionStage());
    }
}

} // namespace MoveBlockChecks
