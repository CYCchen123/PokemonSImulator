#pragma once

#include <sqlite3.h>
#include <string>
#include <map>
#include <vector>
#include <nlohmann/json.hpp>
#include "battle/Species.h"
#include "battle/Moves.h"

/**
 * SQLite-based game database. Replaces data/*.json file loading.
 * Singleton — opens pokemon.db on first use.
 */
class GameDatabase {
public:
    static GameDatabase& instance();

    bool open(const std::string& dbPath = "data/pokemon.db");

    // ---- Species ----
    std::map<int, Species> loadAllSpecies();
    Species loadSpeciesById(int id);

    // ---- Moves ----
    /** Returns moves as JSON (compatible with existing loadMoveRoot) */
    nlohmann::json loadMovesJson();
    /** Returns move data map */
    std::map<int, MoveData> loadAllMoveData();
    MoveData loadMoveDataById(int id);

    // ---- Abilities ----
    nlohmann::json loadAbilitiesJson();
    std::map<int, std::pair<std::string, std::string>> loadAllAbilityData(); // id → {name, desc}

    // ---- Items ----
    nlohmann::json loadItemsJson();
    std::map<int, std::pair<std::string, std::string>> loadAllItemData();

    // ---- Learnsets ----
    std::vector<int> loadLearnsetForSpecies(int speciesId);

private:
    GameDatabase() = default;
    sqlite3* db_ = nullptr;
    std::string resolveDbPath(const std::string& preferred);
};
