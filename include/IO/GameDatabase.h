#pragma once

#include <sqlite3.h>
#include <string>
#include <map>
#include <vector>
#include <nlohmann/json.hpp>
#include "battle/Species.h"
#include "battle/Moves.h"
#include "battle/Abilities.h"
#include "battle/Items.h"

/**
 * SQLite-based game database. Reads all game data from pokemon.db.
 * Singleton — opens on first use.
 */
class GameDatabase {
public:
    static GameDatabase& instance();

    bool open(const std::string& dbPath = "data/pokemon.db");

    // ---- Species ----
    std::map<int, Species> loadAllSpecies();
    Species loadSpeciesById(int id);

    // ---- Moves ----
    nlohmann::json loadMovesJson();
    std::map<int, MoveData> loadAllMoveData();
    MoveData loadMoveDataById(int id);

    // ---- Abilities ----
    nlohmann::json loadAbilitiesJson();
    std::map<int, AbilityData> loadAllAbilityData();

    // ---- Items ----
    nlohmann::json loadItemsJson();
    std::map<int, ItemData> loadAllItemData();

    // ---- Learnsets ----
    std::vector<int> loadLearnsetForSpecies(int speciesId);

private:
    GameDatabase() = default;
    sqlite3* db_ = nullptr;
    std::string resolveDbPath(const std::string& preferred);
};
