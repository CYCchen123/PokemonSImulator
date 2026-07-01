#include "battle/Abilities.h"
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

std::string normalizeName(const std::string& name) {
    std::string out;
    out.reserve(name.size());
    for (char ch : name) {
        if (ch == ' ' || ch == '-' || ch == '\'' || ch == '_') continue;
        out.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(ch))));
    }
    return out;
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

// ---- Fallback hardcoded data ----
AbilityData fallbackAbilityDataById(int id) {
    switch (id) {
        case 1: return {1, "Blaze", "blaze", "When HP is below 1/3, Fire-type moves do 1.5x damage", AbilityType::Blaze};
        case 2: return {2, "Torrent", "torrent", "When HP is below 1/3, Water-type moves do 1.5x damage", AbilityType::Torrent};
        case 3: return {3, "Overgrow", "overgrow", "When HP is below 1/3, Grass-type moves do 1.5x damage", AbilityType::Overgrow};
        case 4: return {4, "Intimidate", "intimidate", "Lowers the foe's Attack stat on entry", AbilityType::Intimidate};
        case 5: return {5, "Multiscale", "multiscale", "Reduces damage when at full HP", AbilityType::Multiscale};
        case 9: return {9, "Static", "static", "Contact with the Pokemon may cause paralysis.", AbilityType::Static};
        case 10: return {10, "Volt Absorb", "volt-absorb", "Restores HP if hit by an Electric-type move.", AbilityType::VoltAbsorb};
        case 11: return {11, "Water Absorb", "water-absorb", "Restores HP if hit by a Water-type move.", AbilityType::WaterAbsorb};
        case 13: return {13, "Cloud Nine", "cloud-nine", "Eliminates the effects of weather.", AbilityType::CloudNine};
        case 15: return {15, "Insomnia", "insomnia", "Prevents the Pokemon from falling asleep.", AbilityType::Insomnia};
        case 17: return {17, "Immunity", "immunity", "Prevents the Pokemon from becoming poisoned.", AbilityType::Immunity};
        case 18: return {18, "Flash Fire", "flash-fire", "Powers up Fire-type moves if hit by one.", AbilityType::FlashFire};
        case 38: return {38, "Poison Point", "poison-point", "Contact with the Pokemon may poison the attacker.", AbilityType::PoisonPoint};
        case 24: return {24, "Rough Skin", "rough-skin", "Damages attackers on contact.", AbilityType::RoughSkin};
        case 22: return {22, "Intimidate", "intimidate", "Lowers the foe's Attack stat on entry", AbilityType::Intimidate};
        case 26: return {26, "Levitate", "levitate", "Gives full immunity to Ground-type moves.", AbilityType::Levitate};
        case 29: return {29, "Clear Body", "clear-body", "Prevents other Pokemon from lowering stats.", AbilityType::ClearBody};
        case 51: return {51, "Keen Eye", "keen-eye", "Prevents other Pokemon from lowering accuracy.", AbilityType::KeenEye};
        case 52: return {52, "Hyper Cutter", "hyper-cutter", "Prevents other Pokemon from lowering Attack.", AbilityType::HyperCutter};
        case 37: return {37, "Huge Power", "huge-power", "Doubles the Pokemon's Attack stat.", AbilityType::HugePower};
        case 39: return {39, "Inner Focus", "inner-focus", "Protects the Pokemon from flinching.", AbilityType::InnerFocus};
        case 47: return {47, "Thick Fat", "thick-fat", "Halves damage from Fire- and Ice-type moves.", AbilityType::ThickFat};
        case 49: return {49, "Flame Body", "flame-body", "Contact with the Pokemon may burn the attacker.", AbilityType::FlameBody};
        case 45: return {45, "Sand Stream", "sand-stream", "Summons a sandstorm in battle.", AbilityType::SandStream};
        case 62: return {62, "Guts", "guts", "Boosts Attack when affected by a major status condition.", AbilityType::Guts};
        case 63: return {63, "Marvel Scale", "marvel-scale", "Boosts Defense when affected by a status condition.", AbilityType::MarvelScale};
        case 72: return {72, "Vital Spirit", "vital-spirit", "Prevents the Pokemon from falling asleep.", AbilityType::VitalSpirit};
        case 73: return {73, "White Smoke", "white-smoke", "Prevents other Pokemon from lowering stats.", AbilityType::WhiteSmoke};
        default: return {0, "None", "none", "", AbilityType::None};
    }
}

// ---- DB-backed cache ----
static std::map<int, AbilityData> g_abilityCache;
static std::once_flag g_abilityCacheFlag;

void ensureAbilityCache() {
    std::call_once(g_abilityCacheFlag, []() {
        auto& db = GameDatabase::instance();
        if (!db.open()) {
            std::cerr << "[AbilityData] Failed to open database" << std::endl;
            return;
        }
        g_abilityCache = db.loadAllAbilityData();
        // Resolve AbilityType from name (GameDatabase doesn't fill this)
        for (auto& [id, ad] : g_abilityCache) {
            if (ad.type == AbilityType::None && !ad.apiName.empty()) {
                ad.type = getAbilityTypeByName(ad.apiName);
            }
        }
    });
}

}  // namespace

// ---- Public API ----

AbilityData getAbilityDataById(int id) {
    if (id <= 0) return {0, "None", "none", "", AbilityType::None};

    ensureAbilityCache();
    auto it = g_abilityCache.find(id);
    if (it != g_abilityCache.end() && it->second.type != AbilityType::None)
        return it->second;

    AbilityData fallback = fallbackAbilityDataById(id);
    if (fallback.id != 0) return fallback;
    return {0, "None", "none", "", AbilityType::None};
}

AbilityData getAbilityDataByName(const std::string& name) {
    const std::string normalized = normalizeName(name);
    ensureAbilityCache();
    for (const auto& [id, ad] : g_abilityCache) {
        if (normalizeName(ad.name) == normalized || normalizeName(ad.apiName) == normalized)
            return ad;
    }
    // Fallback
    for (int id = 1; id <= 100; ++id) {
        AbilityData data = fallbackAbilityDataById(id);
        if (data.id != 0 && (normalizeName(data.name) == normalized || normalizeName(data.apiName) == normalized))
            return data;
    }
    return {0, "None", "none", "", AbilityType::None};
}

AbilityData getAbilityData(AbilityType type) {
    if (type == AbilityType::None) return {0, "None", "none", "", AbilityType::None};
    ensureAbilityCache();
    for (const auto& [id, ad] : g_abilityCache) {
        if (ad.type == type) return ad;
    }
    // Fallback by name matching
    for (int id = 1; id <= 200; ++id) {
        AbilityData data = fallbackAbilityDataById(id);
        if (data.id != 0 && data.type == type) return data;
    }
    return {0, "None", "none", "", AbilityType::None};
}

AbilityType getAbilityTypeById(int id) {
    return getAbilityDataById(id).type;
}

AbilityType getAbilityTypeByNameFromData(const std::string& name) {
    return getAbilityDataByName(name).type;
}
