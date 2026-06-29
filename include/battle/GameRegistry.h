#pragma once

#include "battle/Abilities.h"
#include "battle/Items.h"
#include <functional>
#include <string>
#include <unordered_map>

class Battle;
class Pokemon;
class Move;

using MoveRuleHandler = std::function<bool(BattleContext&, Pokemon*, Pokemon*, const Move&)>;
using AbilityHandler = std::function<void(Ability&)>;
using ItemHandler = std::function<void(Item&)>;

class GameRegistry {
public:
    GameRegistry() = default;

    void init();

    const Ability& getAbility(AbilityType type) const;
    const Item& getItem(ItemType type) const;
    const MoveRuleHandler* getMoveRule(const std::string& normalizedMoveName) const;

    bool applyMoveRule(const std::string& name, BattleContext& ctx,
                       Pokemon* attacker, Pokemon* defender, const Move& move) const;

    bool hasAbility(AbilityType type) const;
    bool hasItem(ItemType type) const;
    bool isInitialized() const { return initialized; }

    void registerMoveRule(const std::string& normalizedMoveName, MoveRuleHandler handler);
    void registerAbility(AbilityType type, AbilityHandler handler);
    void registerItem(ItemType type, ItemHandler handler);

    static GameRegistry& instance();

private:
    bool initialized = false;

private:
    void initAbilities();
    void initItems();
    void initMoveRules();

    std::unordered_map<AbilityType, Ability> abilities;
    std::unordered_map<ItemType, Item> items;
    std::unordered_map<std::string, MoveRuleHandler> moveRules;
    std::unordered_map<AbilityType, AbilityHandler> abilityHandlers;
    std::unordered_map<ItemType, ItemHandler> itemHandlers;
};
