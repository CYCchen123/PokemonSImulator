#include "IO/GameDatabase.h"
#include "battle/Types.h"
#include "battle/Natures.h"
#include <iostream>
#include <filesystem>
#include <cstring>

namespace {

// ---- SQLite helpers ----
struct StmtGuard {
    sqlite3_stmt* stmt;
    ~StmtGuard() { if (stmt) sqlite3_finalize(stmt); }
};

int sqlStep(sqlite3* db, const char* sql, sqlite3_stmt** out) {
    return sqlite3_prepare_v2(db, sql, -1, out, nullptr);
}

Type parseTypeStr(const std::string& s) {
    if (s == "normal") return Type::Normal;
    if (s == "fire") return Type::Fire;
    if (s == "water") return Type::Water;
    if (s == "electric") return Type::Electric;
    if (s == "grass") return Type::Grass;
    if (s == "ice") return Type::Ice;
    if (s == "fighting") return Type::Fighting;
    if (s == "poison") return Type::Poison;
    if (s == "ground") return Type::Ground;
    if (s == "flying") return Type::Flying;
    if (s == "psychic") return Type::Psychic;
    if (s == "bug") return Type::Bug;
    if (s == "rock") return Type::Rock;
    if (s == "ghost") return Type::Ghost;
    if (s == "dragon") return Type::Dragon;
    if (s == "dark") return Type::Dark;
    if (s == "steel") return Type::Steel;
    if (s == "fairy") return Type::Fairy;
    return Type::Count;
}

std::string colText(sqlite3_stmt* stmt, int col) {
    const char* t = reinterpret_cast<const char*>(sqlite3_column_text(stmt, col));
    return t ? std::string(t) : "";
}

} // anonymous namespace

// ============================================================
GameDatabase& GameDatabase::instance() {
    static GameDatabase db;
    return db;
}

std::string GameDatabase::resolveDbPath(const std::string& preferred) {
    if (std::filesystem::exists(preferred)) return preferred;
    for (auto& p : {"../data/pokemon.db", "../../data/pokemon.db"}) {
        if (std::filesystem::exists(p)) return p;
    }
    return preferred;
}

bool GameDatabase::open(const std::string& dbPath) {
    if (db_) return true;
    std::string path = resolveDbPath(dbPath);
    int rc = sqlite3_open(path.c_str(), &db_);
    if (rc != SQLITE_OK) {
        std::cerr << "[DB] Failed to open: " << path << std::endl;
        return false;
    }
    std::cout << "[DB] Opened " << path << std::endl;
    return true;
}

// ---- Species ----
std::map<int, Species> GameDatabase::loadAllSpecies() {
    std::map<int, Species> result;
    if (!db_ && !open()) return result;

    // Load species base data
    sqlite3_stmt* stmt = nullptr;
    sqlStep(db_, "SELECT id, name, type1, type2, base_hp, base_atk, base_def, "
           "base_spa, base_spd, base_spe, height, weight, male_ratio, "
           "evolution_level, next_evolution, egg_group1, egg_group2, hidden_ability "
           "FROM species", &stmt);
    if (!stmt) return result;
    StmtGuard g1{stmt};

    while (sqlite3_step(stmt) == SQLITE_ROW) {
        int id = sqlite3_column_int(stmt, 0);
        Species sp;
        sp.id = id;
        sp.name = colText(stmt, 1);
        sp.type1 = parseTypeStr(colText(stmt, 2));
        std::string t2 = colText(stmt, 3);
        sp.type2 = t2.empty() ? Type::Count : parseTypeStr(t2);
        sp.baseStats[0] = sqlite3_column_int(stmt, 4);
        sp.baseStats[1] = sqlite3_column_int(stmt, 5);
        sp.baseStats[2] = sqlite3_column_int(stmt, 6);
        sp.baseStats[3] = sqlite3_column_int(stmt, 7);
        sp.baseStats[4] = sqlite3_column_int(stmt, 8);
        sp.baseStats[5] = sqlite3_column_int(stmt, 9);
        sp.height = sqlite3_column_int(stmt, 10);
        sp.weight = sqlite3_column_int(stmt, 11);
        sp.maleRatio = static_cast<float>(sqlite3_column_double(stmt, 12));
        sp.evolutionLevel = sqlite3_column_int(stmt, 13);
        sp.nextEvolutionID = sqlite3_column_int(stmt, 14);
        sp.hiddenAbility = static_cast<AbilityType>(sqlite3_column_int(stmt, 17));
        result[id] = std::move(sp);
    }

    // Load abilities (junction)
    sqlite3_stmt* sa_stmt = nullptr;
    sqlStep(db_, "SELECT species_id, ability_id, is_hidden FROM species_abilities", &sa_stmt);
    if (sa_stmt) {
        StmtGuard g2{sa_stmt};
        while (sqlite3_step(sa_stmt) == SQLITE_ROW) {
            int sid = sqlite3_column_int(sa_stmt, 0);
            int aid = sqlite3_column_int(sa_stmt, 1);
            int hidden = sqlite3_column_int(sa_stmt, 2);
            auto it = result.find(sid);
            if (it != result.end()) {
                if (hidden)
                    it->second.hiddenAbility = static_cast<AbilityType>(aid);
                else
                    it->second.abilities.push_back(static_cast<AbilityType>(aid));
            }
        }
    }

    // Note: learnableMoves are NOT loaded into Species struct (kept as IDs in learnsets table).
    // Use loadLearnsetForSpecies() to get move IDs for a specific species when needed.

    std::cout << "[DB] Loaded " << result.size() << " species" << std::endl;
    return result;
}

Species GameDatabase::loadSpeciesById(int id) {
    Species sp;
    if (!db_ && !open()) return sp;

    sqlite3_stmt* stmt = nullptr;
    sqlStep(db_, ("SELECT id, name, type1, type2, base_hp, base_atk, base_def, "
            "base_spa, base_spd, base_spe, height, weight, male_ratio, "
            "evolution_level, next_evolution, egg_group1, egg_group2, hidden_ability "
            "FROM species WHERE id=" + std::to_string(id)).c_str(), &stmt);
    if (!stmt) return sp;
    StmtGuard g{stmt};

    if (sqlite3_step(stmt) == SQLITE_ROW) {
        sp.id = sqlite3_column_int(stmt, 0);
        sp.name = colText(stmt, 1);
        sp.type1 = parseTypeStr(colText(stmt, 2));
        std::string t2 = colText(stmt, 3);
        sp.type2 = t2.empty() ? Type::Count : parseTypeStr(t2);
        for (int i = 0; i < 6; i++) sp.baseStats[i] = sqlite3_column_int(stmt, 4 + i);
        sp.hiddenAbility = static_cast<AbilityType>(sqlite3_column_int(stmt, 17));
    }

    // Load abilities
    sqlite3_stmt* sa = nullptr;
    sqlStep(db_, ("SELECT ability_id, is_hidden FROM species_abilities WHERE species_id=" + std::to_string(id)).c_str(), &sa);
    if (sa) {
        StmtGuard g2{sa};
        while (sqlite3_step(sa) == SQLITE_ROW) {
            int aid = sqlite3_column_int(sa, 0);
            if (sqlite3_column_int(sa, 1)) sp.hiddenAbility = static_cast<AbilityType>(aid);
            else sp.abilities.push_back(static_cast<AbilityType>(aid));
        }
    }

    return sp;
}

// ---- Moves ----
nlohmann::json GameDatabase::loadMovesJson() {
    using json = nlohmann::json;
    json root;
    root["moves"] = json::array();
    if (!db_ && !open()) return root;

    sqlite3_stmt* stmt = nullptr;
    sqlStep(db_, "SELECT id, name, api_name, type, category, power, accuracy, pp, "
           "priority, target, effect, effect_chance, effect_param1, effect_param2, description FROM moves", &stmt);
    if (!stmt) return root;
    StmtGuard g{stmt};

    auto& arr = root["moves"];
    while (sqlite3_step(stmt) == SQLITE_ROW) {
        json mv;
        mv["id"] = sqlite3_column_int(stmt, 0);
        mv["name"] = colText(stmt, 1);
        mv["apiName"] = colText(stmt, 2);
        mv["type"] = colText(stmt, 3);
        mv["category"] = colText(stmt, 4);
        mv["power"] = sqlite3_column_int(stmt, 5);
        mv["accuracy"] = sqlite3_column_int(stmt, 6);
        mv["pp"] = sqlite3_column_int(stmt, 7);
        mv["priority"] = sqlite3_column_int(stmt, 8);
        mv["target"] = colText(stmt, 9);
        mv["effect"] = colText(stmt, 10);
        mv["effectChance"] = sqlite3_column_int(stmt, 11);
        mv["effectParam1"] = sqlite3_column_int(stmt, 12);
        mv["effectParam2"] = sqlite3_column_int(stmt, 13);
        mv["description"] = colText(stmt, 14);
        arr.push_back(std::move(mv));
    }
    return root;
}

std::map<int, MoveData> GameDatabase::loadAllMoveData() {
    std::map<int, MoveData> result;
    if (!db_ && !open()) return result;

    sqlite3_stmt* stmt = nullptr;
    sqlStep(db_, "SELECT id, name, api_name, type, category, power, accuracy, pp, "
           "priority, target, effect, effect_chance, description FROM moves", &stmt);
    if (!stmt) return result;
    StmtGuard g{stmt};

    while (sqlite3_step(stmt) == SQLITE_ROW) {
        MoveData md;
        md.id = sqlite3_column_int(stmt, 0);
        md.name = colText(stmt, 1);
        md.apiName = colText(stmt, 2);
        md.description = colText(stmt, 13);
        // type, category, effect, target parsed later by parseMoveEntry
        result[md.id] = md;
    }
    return result;
}

MoveData GameDatabase::loadMoveDataById(int id) {
    MoveData md;
    if (!db_ && !open()) return md;

    sqlite3_stmt* stmt = nullptr;
    sqlStep(db_, ("SELECT id, name, api_name, type, category, power, accuracy, pp, "
            "priority, target, effect, effect_chance, description FROM moves WHERE id=" + std::to_string(id)).c_str(), &stmt);
    if (!stmt) return md;
    StmtGuard g{stmt};

    if (sqlite3_step(stmt) == SQLITE_ROW) {
        md.id = sqlite3_column_int(stmt, 0);
        md.name = colText(stmt, 1);
        md.apiName = colText(stmt, 2);
        md.type = parseTypeStr(colText(stmt, 3));
        // parseCategory, parseEffect etc.
    }
    return md;
}

// ---- Abilities ----
nlohmann::json GameDatabase::loadAbilitiesJson() {
    using json = nlohmann::json;
    json root;
    root["abilities"] = json::array();
    if (!db_ && !open()) return root;

    sqlite3_stmt* stmt = nullptr;
    sqlStep(db_, "SELECT id, name, api_name, description FROM abilities", &stmt);
    if (!stmt) return root;
    StmtGuard g{stmt};

    while (sqlite3_step(stmt) == SQLITE_ROW) {
        json ab;
        ab["id"] = sqlite3_column_int(stmt, 0);
        ab["name"] = colText(stmt, 1);
        ab["apiName"] = colText(stmt, 2);
        ab["description"] = colText(stmt, 3);
        root["abilities"].push_back(std::move(ab));
    }
    return root;
}

// ---- Items ----
nlohmann::json GameDatabase::loadItemsJson() {
    using json = nlohmann::json;
    json root;
    root["items"] = json::array();
    if (!db_ && !open()) return root;

    sqlite3_stmt* stmt = nullptr;
    sqlStep(db_, "SELECT id, name, api_name, description, is_battle FROM items", &stmt);
    if (!stmt) return root;
    StmtGuard g{stmt};

    while (sqlite3_step(stmt) == SQLITE_ROW) {
        json it;
        it["id"] = sqlite3_column_int(stmt, 0);
        it["name"] = colText(stmt, 1);
        it["apiName"] = colText(stmt, 2);
        it["description"] = colText(stmt, 3);
        it["isBattle"] = sqlite3_column_int(stmt, 4);
        root["items"].push_back(std::move(it));
    }
    return root;
}

std::vector<int> GameDatabase::loadLearnsetForSpecies(int speciesId) {
    std::vector<int> result;
    if (!db_ && !open()) return result;

    sqlite3_stmt* stmt = nullptr;
    sqlStep(db_, ("SELECT move_id FROM learnsets WHERE species_id=" + std::to_string(speciesId) + " ORDER BY move_id").c_str(), &stmt);
    if (!stmt) return result;
    StmtGuard g{stmt};

    while (sqlite3_step(stmt) == SQLITE_ROW)
        result.push_back(sqlite3_column_int(stmt, 0));
    return result;
}
