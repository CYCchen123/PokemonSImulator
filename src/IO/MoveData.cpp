#include "battle/Moves.h"
#include "IO/GameDatabase.h"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <mutex>
#include <vector>

#include <nlohmann/json.hpp>

using json = nlohmann::json;

namespace {

// ---- String utilities ----
std::string toLower(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    return s;
}

std::string trim(const std::string& s) {
    size_t start = 0;
    while (start < s.size() && std::isspace(static_cast<unsigned char>(s[start]))) ++start;
    size_t end = s.size();
    while (end > start && std::isspace(static_cast<unsigned char>(s[end - 1]))) --end;
    return s.substr(start, end - start);
}

std::string normalizeName(const std::string& name) {
    std::string normalized;
    normalized.reserve(name.size());
    for (char ch : name) {
        if (ch == ' ' || ch == '\'' || ch == '-') continue;
        normalized.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(ch))));
    }
    return normalized;
}

std::string slugToDisplayName(const std::string& slug) {
    std::string result;
    bool upper = true;
    for (char ch : slug) {
        if (ch == '-') { result.push_back(' '); upper = true; continue; }
        if (upper && std::isalpha(static_cast<unsigned char>(ch))) {
            result.push_back(static_cast<char>(std::toupper(static_cast<unsigned char>(ch))));
            upper = false;
        } else {
            result.push_back(ch);
            upper = false;
        }
    }
    return result;
}

// ---- Enum parsers (used for fallback data) ----
Type parseType(const std::string& value) {
    const std::string v = toLower(trim(value));
    if (v == "fire") return Type::Fire;
    if (v == "water") return Type::Water;
    if (v == "grass") return Type::Grass;
    if (v == "electric") return Type::Electric;
    if (v == "ice") return Type::Ice;
    if (v == "fighting") return Type::Fighting;
    if (v == "poison") return Type::Poison;
    if (v == "ground") return Type::Ground;
    if (v == "flying") return Type::Flying;
    if (v == "psychic") return Type::Psychic;
    if (v == "bug") return Type::Bug;
    if (v == "rock") return Type::Rock;
    if (v == "ghost") return Type::Ghost;
    if (v == "dragon") return Type::Dragon;
    if (v == "dark") return Type::Dark;
    if (v == "steel") return Type::Steel;
    if (v == "fairy") return Type::Fairy;
    return Type::Normal;
}

Category parseCategory(const std::string& value) {
    const std::string v = toLower(trim(value));
    if (v == "physical") return Category::Physical;
    if (v == "special") return Category::Special;
    return Category::Status;
}

MoveEffect parseEffect(const std::string& value) {
    const std::string v = toLower(trim(value));
    if (v == "pursuit") return MoveEffect::Pursuit;
    if (v == "encore") return MoveEffect::Encore;
    if (v == "dig") return MoveEffect::Dig;
    if (v == "round") return MoveEffect::Round;
    if (v == "knockoff" || v == "knock_off" || v == "knock-off") return MoveEffect::KnockOff;
    if (v == "weatherball" || v == "weather_ball" || v == "weather-ball") return MoveEffect::WeatherBall;
    if (v == "burn") return MoveEffect::Burn;
    if (v == "freeze") return MoveEffect::Freeze;
    if (v == "poison" || v == "bad-poison" || v == "badly-poisoned") return MoveEffect::Poison;
    if (v == "paralyze" || v == "paralysis") return MoveEffect::Paralyze;
    if (v == "sleep") return MoveEffect::Sleep;
    if (v == "confuse" || v == "confusion") return MoveEffect::Confuse;
    if (v == "drain") return MoveEffect::Drain;
    if (v == "recoil") return MoveEffect::Recoil;
    if (v == "flinch") return MoveEffect::Flinch;
    if (v == "safeguard" || v == "protect") return MoveEffect::Safeguard;
    if (v == "statchange" || v == "stat_change") return MoveEffect::StatChange;
    return MoveEffect::None;
}

Target parseTarget(const std::string& value) {
    const std::string v = toLower(trim(value));
    if (v == "user") return Target::Self;
    if (v == "ally") return Target::Ally;
    if (v == "all-allies") return Target::AllAllies;
    if (v == "all-opponents") return Target::AllOpponents;
    if (v == "all-pokemon" || v == "everyone") return Target::All;
    return Target::Opponent;
}

int parseStatIndex(const std::string& statName) {
    const std::string key = toLower(trim(statName));
    if (key == "attack") return 1;
    if (key == "defense") return 2;
    if (key == "special-attack") return 3;
    if (key == "special-defense") return 4;
    if (key == "speed") return 5;
    return 0;
}

// ---- Fallback data ----
MoveData fallbackMoveDataById(int id) {
    switch (id) {
        case 1: return {1, "Ember", "ember", "A small fire attack that may burn the target", Type::Fire, Category::Special, 40, 100, 25, MoveEffect::Burn, 10, 0, 0, 0, Target::Opponent};
        case 2: return {2, "Dragon Claw", "dragon-claw", "A sharp claw attack with dragon power", Type::Dragon, Category::Physical, 80, 100, 15, MoveEffect::None, 0, 0, 0, 0, Target::Opponent};
        case 3: return {3, "Fly", "fly", "Flies up on the first turn, attacks on the second", Type::Flying, Category::Physical, 90, 95, 15, MoveEffect::None, 0, 0, 0, 0, Target::Opponent};
        case 4: return {4, "Earthquake", "earthquake", "A powerful ground attack that hits all Pokemon on the field", Type::Ground, Category::Physical, 100, 100, 10, MoveEffect::None, 0, 0, 0, 0, Target::AllOpponents};
        case 5: return {5, "Water Gun", "water-gun", "A basic water attack", Type::Water, Category::Special, 40, 100, 25, MoveEffect::None, 0, 0, 0, 0, Target::Opponent};
        case 6: return {6, "Hydro Pump", "hydro-pump", "A powerful water attack with low accuracy", Type::Water, Category::Special, 110, 80, 5, MoveEffect::None, 0, 0, 0, 0, Target::Opponent};
        case 7: return {7, "Ice Beam", "ice-beam", "An ice attack that may freeze the target", Type::Ice, Category::Special, 90, 100, 10, MoveEffect::Freeze, 10, 0, 0, 0, Target::Opponent};
        case 8: return {8, "Protect", "protect", "Protects the user from attacks for one turn", Type::Normal, Category::Status, 0, 100, 10, MoveEffect::Safeguard, 100, 0, 0, 4, Target::Self};
        default: return {0, "", "", "", Type::Normal, Category::Status, 0, 100, 0, MoveEffect::None, 0, 0, 0, 0, Target::Opponent};
    }
}

MoveData defaultTackleData() {
    return {0, "Tackle", "tackle", "Fallback move", Type::Normal, Category::Physical, 40, 100, 35, MoveEffect::None, 0, 0, 0, 0, Target::Opponent};
}

// ---- DB-backed cache ----
static std::map<int, MoveData> g_moveCache;
static std::once_flag g_moveCacheFlag;

void ensureMoveCache() {
    std::call_once(g_moveCacheFlag, []() {
        auto& db = GameDatabase::instance();
        if (!db.open()) {
            std::cerr << "[MoveData] Failed to open database" << std::endl;
            return;
        }
        g_moveCache = db.loadAllMoveData();
    });
}

}  // namespace

// ---- Public API ----
MoveData getMoveDataById(int id) {
    if (id <= 0) return defaultTackleData();

    ensureMoveCache();
    auto it = g_moveCache.find(id);
    if (it != g_moveCache.end()) return it->second;

    // Fallback to hardcoded data
    MoveData legacy = fallbackMoveDataById(id);
    if (legacy.id != 0) return legacy;
    return defaultTackleData();
}

MoveData getMoveDataByName(const std::string& name) {
    const std::string normalized = normalizeName(name);
    ensureMoveCache();
    for (const auto& [id, data] : g_moveCache) {
        if (normalizeName(data.name) == normalized || normalizeName(data.apiName) == normalized)
            return data;
    }
    // Fallback
    for (int id = 1; id <= 8; ++id) {
        MoveData data = fallbackMoveDataById(id);
        if (normalizeName(data.name) == normalized || normalizeName(data.apiName) == normalized)
            return data;
    }
    return defaultTackleData();
}

Move createMoveFromData(const MoveData& data) { return Move(data); }
Move createMoveById(int id) { return createMoveFromData(getMoveDataById(id)); }
Move createMoveByName(const std::string& name) { return createMoveFromData(getMoveDataByName(name)); }
