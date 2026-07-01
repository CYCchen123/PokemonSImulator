#include "battle/Items.h"
#include "IO/GameDatabase.h"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <mutex>
#include <unordered_map>
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

std::string normalizeName(const std::string& s) {
    std::string out;
    out.reserve(s.size());
    for (char ch : s) {
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

// ---- ItemType resolution ----
ItemType parseMappedItemType(const std::string& mapped) {
    const std::string key = normalizeName(mapped);
    static const std::unordered_map<std::string, ItemType> kAliasMap = {
        {"oddincense", ItemType::TwistedSpoon},
        {"rockincense", ItemType::HardStone},
        {"waveincense", ItemType::MysticWater},
        {"roseincense", ItemType::MiracleSeed},
        {"dracoplate", ItemType::DragonFang},
        {"dreadplate", ItemType::BlackGlasses},
        {"firegem", ItemType::Charcoal},
        {"watergem", ItemType::MysticWater},
        {"electricgem", ItemType::Magnet},
        {"grassgem", ItemType::MiracleSeed},
        {"icegem", ItemType::NeverMeltIce},
        {"fightinggem", ItemType::BlackBelt},
        {"poisongem", ItemType::PoisonBarb},
        {"groundgem", ItemType::EarthPlate},
        {"flyinggem", ItemType::SharpBeak},
        {"psychicgem", ItemType::TwistedSpoon},
        {"buggem", ItemType::SilverPowder},
        {"rockgem", ItemType::HardStone},
        {"ghostgem", ItemType::SpellTag},
        {"darkgem", ItemType::BlackGlasses},
        {"steelgem", ItemType::MetalCoat},
        {"dragongem", ItemType::DragonFang},
        {"normalgem", ItemType::SilkScarf}
    };

    auto aliasIt = kAliasMap.find(key);
    if (aliasIt != kAliasMap.end()) return aliasIt->second;

    if (key.rfind("dynamaxcrystalgem", 0) == 0) return ItemType::None;

    for (int i = 0; i < static_cast<int>(ItemType::Count); ++i) {
        ItemType t = static_cast<ItemType>(i);
        if (normalizeName(getItemName(t)) == key) return t;
    }
    return ItemType::None;
}

// ---- DB-backed cache ----
static std::map<int, ItemData> g_itemCache;
static std::once_flag g_itemCacheFlag;

void ensureItemCache() {
    std::call_once(g_itemCacheFlag, []() {
        auto& db = GameDatabase::instance();
        if (!db.open()) {
            std::cerr << "[ItemData] Failed to open database" << std::endl;
            return;
        }
        g_itemCache = db.loadAllItemData();
        // Resolve ItemType from name (GameDatabase doesn't fill this)
        for (auto& [id, idat] : g_itemCache) {
            if (idat.mappedType == ItemType::None && !idat.apiName.empty()) {
                idat.mappedType = parseMappedItemType(idat.apiName);
            }
            if (idat.mappedType == ItemType::None && !idat.name.empty()) {
                idat.mappedType = parseMappedItemType(idat.name);
            }
        }
    });
}

}  // namespace

// ---- Public API ----

ItemData getItemDataById(int id) {
    if (id <= 0) return {0, "None", "none", "", false, ItemType::None};

    ensureItemCache();
    auto it = g_itemCache.find(id);
    if (it != g_itemCache.end()) return it->second;

    return {0, "None", "none", "", false, ItemType::None};
}

ItemData getItemDataByName(const std::string& name) {
    const std::string normalized = normalizeName(name);
    ensureItemCache();
    for (const auto& [id, idat] : g_itemCache) {
        if (normalizeName(idat.name) == normalized || normalizeName(idat.apiName) == normalized)
            return idat;
    }
    return {0, "None", "none", "", false, ItemType::None};
}

ItemType getItemTypeById(int id) { return getItemDataById(id).mappedType; }
ItemType getItemTypeByName(const std::string& name) { return getItemDataByName(name).mappedType; }

Item createItemFromData(const ItemData& data) {
    if (data.mappedType != ItemType::None) return getItem(data.mappedType);
    return Item(ItemType::None, data.name.empty() ? "None" : data.name);
}

Item createItemById(int id) { return createItemFromData(getItemDataById(id)); }
Item createItemByName(const std::string& name) { return createItemFromData(getItemDataByName(name)); }
