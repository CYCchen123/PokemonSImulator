#include "server/db/repositories/DataRepo.h"
#include "server/db/Database.h"

#include <fstream>
#include <iostream>
#include <filesystem>
#include <nlohmann/json.hpp>

namespace server {
namespace db {

namespace fs = std::filesystem;

// ==========================================
// Path resolution
// ==========================================

std::string DataRepo::resolveDataPath(const std::string& filename) {
    // Try multiple search locations
    std::vector<std::string> candidates = {
        "data/" + filename,
        "../data/" + filename,
        "../../data/" + filename,
    };

    // Also try relative to the executable's directory
    // (handled implicitly by the cwd-based search above)

    for (const auto& p : candidates) {
        if (fs::exists(p)) {
            return p;
        }
    }

    // Return the first candidate as default (will fail to open)
    return candidates[0];
}

// ==========================================
// Table helpers
// ==========================================

bool DataRepo::tableHasData(const std::string& tableName) {
    auto& db = Database::instance();
    auto result = db.queryToJson(
        "SELECT COUNT(*) as cnt FROM " + tableName + ";");
    if (result.empty()) return false;
    const auto& row = result[0];
    if (row.contains("cnt") && row["cnt"].is_number()) {
        return row["cnt"].get<int>() > 0;
    }
    return false;
}

// ==========================================
// JSON file loading helper
// ==========================================

namespace {

nlohmann::json loadJsonFile(const std::string& path) {
    std::ifstream input(path);
    if (!input.is_open()) {
        std::cerr << "[DataRepo] Cannot open: " << path << std::endl;
        return nlohmann::json();
    }
    nlohmann::json data = nlohmann::json::parse(input, nullptr, false);
    if (data.is_discarded()) {
        std::cerr << "[DataRepo] Invalid JSON: " << path << std::endl;
        return nlohmann::json();
    }
    return data;
}

// Escape single quotes for SQL
std::string escapeSql(const std::string& s) {
    std::string result;
    result.reserve(s.size() + 8);
    for (char c : s) {
        if (c == '\'') result += "''";
        else result += c;
    }
    return result;
}

} // anonymous namespace

// ==========================================
// Seed: Species
// ==========================================

bool DataRepo::seedSpecies() {
    if (tableHasData("species")) {
        std::cout << "[DataRepo] Species table already has data, skipping" << std::endl;
        return true;
    }

    std::string path = resolveDataPath("species.json");
    std::cout << "[DataRepo] Seeding species from " << path << "..." << std::endl;

    auto data = loadJsonFile(path);
    if (data.is_null()) return false;

    // Species JSON format: { "species": [...] }
    const auto& speciesArray = data.contains("species") ? data["species"] : data;
    if (!speciesArray.is_array()) {
        std::cerr << "[DataRepo] species.json does not contain a 'species' array" << std::endl;
        return false;
    }

    auto& db = Database::instance();
    db.beginTransaction();

    int count = 0;
    for (const auto& sp : speciesArray) {
        int id = sp.value("id", 0);
        std::string name = escapeSql(sp.value("name", "Unknown"));

        // Types
        std::string type1 = "Normal";
        std::string type2;
        if (sp.contains("types") && sp["types"].is_array()) {
            if (sp["types"].size() > 0 && sp["types"][0].is_string())
                type1 = sp["types"][0].get<std::string>();
            if (sp["types"].size() > 1 && sp["types"][1].is_string())
                type2 = sp["types"][1].get<std::string>();
        } else if (sp.contains("type1") && sp["type1"].is_string()) {
            type1 = sp["type1"].get<std::string>();
            if (sp.contains("type2") && sp["type2"].is_string())
                type2 = sp["type2"].get<std::string>();
        }

        // Base stats
        auto getStat = [&](const std::string& key, int defaultVal) -> int {
            if (sp.contains("baseStats") && sp["baseStats"].is_array() && sp["baseStats"].size() >= 6) {
                if (key == "hp") return sp["baseStats"][0].get<int>();
                if (key == "atk") return sp["baseStats"][1].get<int>();
                if (key == "def") return sp["baseStats"][2].get<int>();
                if (key == "spa") return sp["baseStats"][3].get<int>();
                if (key == "spd") return sp["baseStats"][4].get<int>();
                if (key == "spe") return sp["baseStats"][5].get<int>();
            }
            return defaultVal;
        };

        int hp = getStat("hp", 0);
        int atk = getStat("atk", 0);
        int def = getStat("def", 0);
        int spa = getStat("spa", 0);
        int spd = getStat("spd", 0);
        int spe = getStat("spe", 0);

        // Abilities
        std::string abilityIds = "[]";
        if (sp.contains("abilities") && sp["abilities"].is_array()) {
            abilityIds = sp["abilities"].dump();
        }

        int hiddenAbilityId = sp.value("hiddenAbilityID", 0);

        // Egg groups
        std::string eggGroups = "[]";
        if (sp.contains("eggGroups") && sp["eggGroups"].is_array()) {
            eggGroups = sp["eggGroups"].dump();
        }

        // Full JSON blob
        std::string dataJson = escapeSql(sp.dump());

        std::string sql = "INSERT INTO species (id, name, type1, type2, base_hp, base_atk, base_def, "
                          "base_spa, base_spd, base_spe, ability_ids, hidden_ability_id, egg_groups, data_json) "
                          "VALUES (" +
                          std::to_string(id) + ", '" + name + "', '" + escapeSql(type1) + "', '" +
                          escapeSql(type2) + "', " + std::to_string(hp) + ", " + std::to_string(atk) + ", " +
                          std::to_string(def) + ", " + std::to_string(spa) + ", " + std::to_string(spd) + ", " +
                          std::to_string(spe) + ", '" + escapeSql(abilityIds) + "', " +
                          std::to_string(hiddenAbilityId) + ", '" + escapeSql(eggGroups) + "', '" +
                          dataJson + "');";

        if (!db.execute(sql)) {
            std::cerr << "[DataRepo] Failed to insert species id=" << id << std::endl;
            db.rollbackTransaction();
            return false;
        }
        count++;
    }

    db.commitTransaction();
    std::cout << "[DataRepo] Seeded " << count << " species" << std::endl;
    return true;
}

// ==========================================
// Seed: Moves
// ==========================================

bool DataRepo::seedMoves() {
    if (tableHasData("moves")) {
        std::cout << "[DataRepo] Moves table already has data, skipping" << std::endl;
        return true;
    }

    std::string path = resolveDataPath("moves.json");
    std::cout << "[DataRepo] Seeding moves from " << path << "..." << std::endl;

    auto data = loadJsonFile(path);
    if (data.is_null()) return false;

    const auto& movesArray = data.contains("moves") ? data["moves"] : data;
    if (!movesArray.is_array()) {
        std::cerr << "[DataRepo] moves.json does not contain a 'moves' array" << std::endl;
        return false;
    }

    auto& db = Database::instance();
    db.beginTransaction();

    int count = 0;
    for (const auto& mv : movesArray) {
        int id = mv.value("id", 0);
        std::string name = escapeSql(mv.value("name", mv.value("apiName", "Unknown")));
        std::string type = escapeSql(mv.value("type", "Normal"));
        std::string category = escapeSql(mv.value("category", "Status"));
        int power = mv.value("power", 0);
        int accuracy = mv.value("accuracy", 100);
        int pp = mv.value("pp", 0);
        int priority = mv.value("priority", 0);
        std::string target = escapeSql(mv.value("target", "opponent"));
        std::string effect = escapeSql(mv.value("effect", ""));
        int effectChance = mv.value("effectChance", 0);
        std::string dataJson = escapeSql(mv.dump());

        std::string sql = "INSERT INTO moves (id, name, type, category, power, accuracy, pp, priority, "
                          "target, effect, effect_chance, data_json) VALUES (" +
                          std::to_string(id) + ", '" + name + "', '" + type + "', '" + category +
                          "', " + std::to_string(power) + ", " + std::to_string(accuracy) + ", " +
                          std::to_string(pp) + ", " + std::to_string(priority) + ", '" + target +
                          "', '" + effect + "', " + std::to_string(effectChance) + ", '" +
                          dataJson + "');";

        if (!db.execute(sql)) {
            std::cerr << "[DataRepo] Failed to insert move id=" << id << " name=" << name << std::endl;
        }
        count++;
    }

    db.commitTransaction();
    std::cout << "[DataRepo] Seeded " << count << " moves" << std::endl;
    return true;
}

// ==========================================
// Seed: Abilities
// ==========================================

bool DataRepo::seedAbilities() {
    if (tableHasData("abilities")) {
        std::cout << "[DataRepo] Abilities table already has data, skipping" << std::endl;
        return true;
    }

    std::string path = resolveDataPath("abilities.json");
    std::cout << "[DataRepo] Seeding abilities from " << path << "..." << std::endl;

    auto data = loadJsonFile(path);
    if (data.is_null()) return false;

    const auto& abilitiesArray = data.contains("abilities") ? data["abilities"] : data;
    if (!abilitiesArray.is_array()) {
        std::cerr << "[DataRepo] abilities.json does not contain an 'abilities' array" << std::endl;
        return false;
    }

    auto& db = Database::instance();
    db.beginTransaction();

    int count = 0;
    for (const auto& ab : abilitiesArray) {
        int id = ab.value("id", 0);
        std::string name = escapeSql(ab.value("name", ab.value("apiName", "Unknown")));
        std::string dataJson = escapeSql(ab.dump());

        std::string sql = "INSERT INTO abilities (id, name, data_json) VALUES (" +
                          std::to_string(id) + ", '" + name + "', '" + dataJson + "');";

        if (!db.execute(sql)) {
            std::cerr << "[DataRepo] Failed to insert ability id=" << id << std::endl;
        }
        count++;
    }

    db.commitTransaction();
    std::cout << "[DataRepo] Seeded " << count << " abilities" << std::endl;
    return true;
}

// ==========================================
// Seed: Items
// ==========================================

bool DataRepo::seedItems() {
    if (tableHasData("items")) {
        std::cout << "[DataRepo] Items table already has data, skipping" << std::endl;
        return true;
    }

    std::string path = resolveDataPath("items.json");
    std::cout << "[DataRepo] Seeding items from " << path << "..." << std::endl;

    auto data = loadJsonFile(path);
    if (data.is_null()) return false;

    const auto& itemsArray = data.contains("items") ? data["items"] : data;
    if (!itemsArray.is_array()) {
        std::cerr << "[DataRepo] items.json does not contain an 'items' array" << std::endl;
        return false;
    }

    auto& db = Database::instance();
    db.beginTransaction();

    int count = 0;
    for (const auto& it : itemsArray) {
        int id = it.value("id", 0);
        std::string name = escapeSql(it.value("name", it.value("apiName", "Unknown")));
        int isBattle = it.value("isBattle", 1);
        std::string dataJson = escapeSql(it.dump());

        std::string sql = "INSERT INTO items (id, name, is_battle, data_json) VALUES (" +
                          std::to_string(id) + ", '" + name + "', " + std::to_string(isBattle) +
                          ", '" + dataJson + "');";

        if (!db.execute(sql)) {
            std::cerr << "[DataRepo] Failed to insert item id=" << id << std::endl;
        }
        count++;
    }

    db.commitTransaction();
    std::cout << "[DataRepo] Seeded " << count << " items" << std::endl;
    return true;
}

// ==========================================
// Seed: All
// ==========================================

bool DataRepo::seedAllIfEmpty() {
    bool ok = true;
    ok = ok && seedSpecies();
    ok = ok && seedMoves();
    ok = ok && seedAbilities();
    ok = ok && seedItems();
    return ok;
}

// ==========================================
// Enum mappings
// ==========================================

nlohmann::json DataRepo::getEnumMappings() {
    using nlohmann::json;

    json enums;

    // Type
    enums["type"] = {
        {{"value", 0}, {"name", "Normal"}, {"label", "一般"}},
        {{"value", 1}, {"name", "Fire"}, {"label", "火"}},
        {{"value", 2}, {"name", "Water"}, {"label", "水"}},
        {{"value", 3}, {"name", "Electric"}, {"label", "电"}},
        {{"value", 4}, {"name", "Grass"}, {"label", "草"}},
        {{"value", 5}, {"name", "Ice"}, {"label", "冰"}},
        {{"value", 6}, {"name", "Fighting"}, {"label", "格斗"}},
        {{"value", 7}, {"name", "Poison"}, {"label", "毒"}},
        {{"value", 8}, {"name", "Ground"}, {"label", "地面"}},
        {{"value", 9}, {"name", "Flying"}, {"label", "飞行"}},
        {{"value", 10}, {"name", "Psychic"}, {"label", "超能力"}},
        {{"value", 11}, {"name", "Bug"}, {"label", "虫"}},
        {{"value", 12}, {"name", "Rock"}, {"label", "岩石"}},
        {{"value", 13}, {"name", "Ghost"}, {"label", "幽灵"}},
        {{"value", 14}, {"name", "Dragon"}, {"label", "龙"}},
        {{"value", 15}, {"name", "Dark"}, {"label", "恶"}},
        {{"value", 16}, {"name", "Steel"}, {"label", "钢"}},
        {{"value", 17}, {"name", "Fairy"}, {"label", "妖精"}}
    };

    // Category
    enums["category"] = {
        {{"value", 0}, {"name", "Physical"}, {"label", "物理"}},
        {{"value", 1}, {"name", "Special"}, {"label", "特殊"}},
        {{"value", 2}, {"name", "Status"}, {"label", "变化"}}
    };

    // WeatherType
    enums["weather"] = {
        {{"value", 0}, {"name", "Clear"}, {"label", "无天气"}},
        {{"value", 1}, {"name", "Rain"}, {"label", "雨天"}},
        {{"value", 2}, {"name", "Sun"}, {"label", "晴天"}},
        {{"value", 3}, {"name", "Sandstorm"}, {"label", "沙暴"}},
        {{"value", 4}, {"name", "Hail"}, {"label", "冰雹"}},
        {{"value", 5}, {"name", "Snow"}, {"label", "雪天"}}
    };

    // FieldType
    enums["field"] = {
        {{"value", 0}, {"name", "None"}, {"label", "无场地"}},
        {{"value", 1}, {"name", "Psychic"}, {"label", "精神场地"}},
        {{"value", 2}, {"name", "Electric"}, {"label", "电气场地"}},
        {{"value", 3}, {"name", "Grassy"}, {"label", "青草场地"}},
        {{"value", 4}, {"name", "Misty"}, {"label", "薄雾场地"}},
        {{"value", 5}, {"name", "TrickRoom"}, {"label", "戏法空间"}}
    };

    // StatusType
    enums["status"] = {
        {{"value", 0}, {"name", "None"}, {"label", "无状态"}},
        {{"value", 1}, {"name", "Burn"}, {"label", "灼伤"}},
        {{"value", 2}, {"name", "Freeze"}, {"label", "冰冻"}},
        {{"value", 3}, {"name", "Paralysis"}, {"label", "麻痹"}},
        {{"value", 4}, {"name", "Poison"}, {"label", "中毒"}},
        {{"value", 5}, {"name", "Sleep"}, {"label", "睡眠"}},
        {{"value", 6}, {"name", "Flinch"}, {"label", "畏缩"}},
        {{"value", 7}, {"name", "ToxicPoison"}, {"label", "剧毒"}},
        {{"value", 8}, {"name", "Confusion"}, {"label", "混乱"}}
    };

    // ActionType
    enums["action"] = {
        {{"value", 0}, {"name", "Attack"}, {"label", "攻击"}},
        {{"value", 1}, {"name", "Switch"}, {"label", "换人"}},
        {{"value", 2}, {"name", "UseItem"}, {"label", "使用道具"}},
        {{"value", 3}, {"name", "Pass"}, {"label", "跳过"}}
    };

    // Nature
    enums["nature"] = json::array({
        {{"value", 0}, {"name", "Hardy"}, {"boostedStat", ""}, {"reducedStat", ""}},
        {{"value", 1}, {"name", "Lonely"}, {"boostedStat", "atk"}, {"reducedStat", "def"}},
        {{"value", 2}, {"name", "Brave"}, {"boostedStat", "atk"}, {"reducedStat", "spe"}},
        {{"value", 3}, {"name", "Adamant"}, {"boostedStat", "atk"}, {"reducedStat", "spa"}},
        {{"value", 4}, {"name", "Naughty"}, {"boostedStat", "atk"}, {"reducedStat", "spd"}},
        {{"value", 5}, {"name", "Bold"}, {"boostedStat", "def"}, {"reducedStat", "atk"}},
        {{"value", 6}, {"name", "Docile"}, {"boostedStat", ""}, {"reducedStat", ""}},
        {{"value", 7}, {"name", "Relaxed"}, {"boostedStat", "def"}, {"reducedStat", "spe"}},
        {{"value", 8}, {"name", "Impish"}, {"boostedStat", "def"}, {"reducedStat", "spa"}},
        {{"value", 9}, {"name", "Lax"}, {"boostedStat", "def"}, {"reducedStat", "spd"}},
        {{"value", 10}, {"name", "Timid"}, {"boostedStat", "spe"}, {"reducedStat", "atk"}},
        {{"value", 11}, {"name", "Hasty"}, {"boostedStat", "spe"}, {"reducedStat", "def"}},
        {{"value", 12}, {"name", "Serious"}, {"boostedStat", ""}, {"reducedStat", ""}},
        {{"value", 13}, {"name", "Jolly"}, {"boostedStat", "spe"}, {"reducedStat", "spa"}},
        {{"value", 14}, {"name", "Naive"}, {"boostedStat", "spe"}, {"reducedStat", "spd"}},
        {{"value", 15}, {"name", "Modest"}, {"boostedStat", "spa"}, {"reducedStat", "atk"}},
        {{"value", 16}, {"name", "Mild"}, {"boostedStat", "spa"}, {"reducedStat", "def"}},
        {{"value", 17}, {"name", "Quiet"}, {"boostedStat", "spa"}, {"reducedStat", "spe"}},
        {{"value", 18}, {"name", "Bashful"}, {"boostedStat", ""}, {"reducedStat", ""}},
        {{"value", 19}, {"name", "Rash"}, {"boostedStat", "spa"}, {"reducedStat", "spd"}},
        {{"value", 20}, {"name", "Calm"}, {"boostedStat", "spd"}, {"reducedStat", "atk"}},
        {{"value", 21}, {"name", "Gentle"}, {"boostedStat", "spd"}, {"reducedStat", "def"}},
        {{"value", 22}, {"name", "Sassy"}, {"boostedStat", "spd"}, {"reducedStat", "spe"}},
        {{"value", 23}, {"name", "Careful"}, {"boostedStat", "spd"}, {"reducedStat", "spa"}},
        {{"value", 24}, {"name", "Quirky"}, {"boostedStat", ""}, {"reducedStat", ""}}
    });

    // StatIndex
    enums["stat"] = {
        {{"value", 0}, {"name", "HP"}, {"label", "HP"}},
        {{"value", 1}, {"name", "Attack"}, {"label", "攻击"}},
        {{"value", 2}, {"name", "Defense"}, {"label", "防御"}},
        {{"value", 3}, {"name", "SpecialAttack"}, {"label", "特攻"}},
        {{"value", 4}, {"name", "SpecialDefense"}, {"label", "特防"}},
        {{"value", 5}, {"name", "Speed"}, {"label", "速度"}},
        {{"value", 6}, {"name", "Accuracy"}, {"label", "命中率"}},
        {{"value", 7}, {"name", "Evasion"}, {"label", "闪避率"}}
    };

    // Target
    enums["target"] = {
        {{"value", 0}, {"name", "Self"}, {"label", "自身"}},
        {{"value", 1}, {"name", "Ally"}, {"label", "队友"}},
        {{"value", 2}, {"name", "Opponent"}, {"label", "对手"}},
        {{"value", 3}, {"name", "AllAllies"}, {"label", "所有队友"}},
        {{"value", 4}, {"name", "AllOpponents"}, {"label", "所有对手"}},
        {{"value", 5}, {"name", "All"}, {"label", "全场"}}
    };

    // EggGroup
    enums["eggGroup"] = {
        {{"value", 0}, {"name", "None"}, {"label", "无"}},
        {{"value", 1}, {"name", "Monster"}, {"label", "怪兽"}},
        {{"value", 2}, {"name", "Water1"}, {"label", "水中1"}},
        {{"value", 3}, {"name", "Water2"}, {"label", "水中2"}},
        {{"value", 4}, {"name", "Bug"}, {"label", "虫"}},
        {{"value", 5}, {"name", "Flying"}, {"label", "飞行"}},
        {{"value", 6}, {"name", "Field"}, {"label", "陆上"}},
        {{"value", 7}, {"name", "Fairy"}, {"label", "妖精"}},
        {{"value", 8}, {"name", "HumanLike"}, {"label", "人形"}},
        {{"value", 9}, {"name", "Mineral"}, {"label", "矿物"}},
        {{"value", 10}, {"name", "Amorphous"}, {"label", "不定形"}},
        {{"value", 11}, {"name", "Ditto"}, {"label", "百变怪"}},
        {{"value", 12}, {"name", "Dragon"}, {"label", "龙"}},
        {{"value", 13}, {"name", "Undiscovered"}, {"label", "未发现"}}
    };

    // Trigger
    enums["trigger"] = {
        {{"value", 0}, {"name", "OnEntry"}, {"label", "上场时"}},
        {{"value", 1}, {"name", "OnExit"}, {"label", "离场时"}},
        {{"value", 2}, {"name", "OnTurnStart"}, {"label", "回合开始时"}},
        {{"value", 3}, {"name", "OnTurnEnd"}, {"label", "回合结束时"}},
        {{"value", 4}, {"name", "OnDamage"}, {"label", "受到伤害时"}},
        {{"value", 5}, {"name", "OnDealDamage"}, {"label", "造成伤害时"}},
        {{"value", 6}, {"name", "OnAttack"}, {"label", "攻击时"}},
        {{"value", 7}, {"name", "OnFaint"}, {"label", "濒死时"}},
        {{"value", 8}, {"name", "OnStatusInflicted"}, {"label", "施加状态时"}},
        {{"value", 9}, {"name", "OnWeatherChange"}, {"label", "天气改变时"}},
        {{"value", 10}, {"name", "OnTerrainChange"}, {"label", "场地改变时"}}
    };

    return enums;
}

} // namespace db
} // namespace server
