#include "IO/LearnsetData.h"

#include <curl/curl.h>
#include <nlohmann/json.hpp>
#include <fstream>
#include <iostream>
#include <optional>
#include <set>
#include <filesystem>

using json = nlohmann::json;

namespace {

// ============================================================
// curl helpers (same pattern as MoveData.cpp)
// ============================================================
size_t curlWriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    const size_t total = size * nmemb;
    auto* out = static_cast<std::string*>(userp);
    out->append(static_cast<char*>(contents), total);
    return total;
}

bool fetchPokemonPayload(int speciesId, json& outPayload) {
    CURL* curl = curl_easy_init();
    if (!curl) return false;

    std::string response;
    const std::string url = "https://pokeapi.co/api/v2/pokemon/" + std::to_string(speciesId);

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, curlWriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 15L);
    curl_easy_setopt(curl, CURLOPT_USERAGENT, "PokemonSimulator/1.0");

    const CURLcode res = curl_easy_perform(curl);
    long statusCode = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &statusCode);
    curl_easy_cleanup(curl);

    if (res != CURLE_OK) return false;
    if (statusCode != 200) return false;

    outPayload = json::parse(response, nullptr, false);
    return !outPayload.is_discarded();
}

std::vector<int> extractMoveIds(const json& payload) {
    std::vector<int> moveIds;
    const auto& moves = payload.value("moves", json::array());
    for (const auto& entry : moves) {
        const std::string url = entry.value("move", json::object()).value("url", "");
        // URL format: https://pokeapi.co/api/v2/move/{id}/
        try {
            size_t lastSlash = url.rfind('/', url.size() - 2);
            if (lastSlash != std::string::npos) {
                std::string idStr = url.substr(lastSlash + 1, url.size() - lastSlash - 2);
                int moveId = std::stoi(idStr);
                moveIds.push_back(moveId);
            }
        } catch (...) {}
    }
    std::sort(moveIds.begin(), moveIds.end());
    return moveIds;
}

bool loadJsonFile(const std::string& path, json& out) {
    std::ifstream f(path);
    if (!f.is_open()) return false;
    out = json::parse(f, nullptr, false);
    return !out.is_discarded();
}

bool saveJsonFile(const std::string& path, const json& data) {
    std::ofstream f(path);
    if (!f.is_open()) return false;
    f << data.dump(2);
    return true;
}

// Resolve data file path with fallback search.
// For existing files: return the first candidate that exists.
// For new files: try to create in the first writable data/ directory found.
std::string resolveDataPath(const std::string& filename) {
    std::vector<std::string> candidates = {
        "data/" + filename,
        "../data/" + filename,
        "../../data/" + filename,
    };
    // For existing files, return first match
    for (const auto& p : candidates) {
        if (std::filesystem::exists(p)) return p;
    }
    // For new files, find the first data/ directory that exists
    for (const auto& p : candidates) {
        std::string dir = p.substr(0, p.rfind('/'));
        if (std::filesystem::exists(dir) || dir.empty()) return p;
    }
    return "data/" + filename;
}

} // anonymous namespace

bool prefetchLearnsetsFromPokeAPI(bool refresh) {
    // Load species
    json speciesData;
    std::string speciesPath = resolveDataPath("species.json");
    if (!loadJsonFile(speciesPath, speciesData)) {
        std::cerr << "[Learnset] Failed to load species.json from " << speciesPath << std::endl;
        return false;
    }

    auto& speciesList = speciesData.contains("species") ? speciesData["species"] : speciesData;
    if (!speciesList.is_array()) {
        std::cerr << "[Learnset] Invalid species.json format" << std::endl;
        return false;
    }

    // Load existing learnsets
    json learnsets;
    std::string learnsetPath = resolveDataPath("learnsets.json");
    loadJsonFile(learnsetPath, learnsets);
    if (!learnsets.is_object()) learnsets = json::object();

    int total = speciesList.size();
    int fetched = 0;
    int skipped = 0;

    std::cout << "[Learnset] " << total << " species to check..." << std::endl;

    for (int i = 0; i < total; ++i) {
        auto& sp = speciesList[i];
        int sid = sp.value("id", 0);
        std::string sidStr = std::to_string(sid);

        // Skip if already fetched and not refreshing
        if (!refresh && learnsets.contains(sidStr)) {
            skipped++;
            continue;
        }

        // Fetch from PokeAPI
        json payload;
        if (!fetchPokemonPayload(sid, payload)) {
            std::cerr << "[Learnset] Failed to fetch species " << sid << std::endl;
            continue;
        }

        auto moveIds = extractMoveIds(payload);
        learnsets[sidStr] = moveIds;
        sp["learnableMoves"] = moveIds;

        // Also extract abilities from the same payload
        std::vector<int> abilityIds;
        std::optional<int> hiddenAbility;
        for (const auto& abEntry : payload.value("abilities", json::array())) {
            const auto& ab = abEntry.value("ability", json::object());
            const std::string abUrl = ab.value("url", "");
            try {
                size_t lastSlash = abUrl.rfind('/', abUrl.size() - 2);
                if (lastSlash != std::string::npos) {
                    int abId = std::stoi(abUrl.substr(lastSlash + 1, abUrl.size() - lastSlash - 2));
                    if (abEntry.value("is_hidden", false)) hiddenAbility = abId;
                    else abilityIds.push_back(abId);
                }
            } catch (...) {}
        }
        sp["abilities"] = abilityIds;
        if (hiddenAbility.has_value()) sp["hiddenAbilityID"] = *hiddenAbility;
        fetched++;

        if ((i + 1) % 20 == 0) {
            std::cout << "[Learnset] Progress: " << (i + 1) << "/" << total
                      << " (" << fetched << " fetched)" << std::endl;
        }
    }

    // Save learnsets.json
    if (!saveJsonFile(learnsetPath, learnsets)) {
        std::cerr << "[Learnset] Failed to save learnsets.json" << std::endl;
        return false;
    }

    // Save updated species.json
    if (!saveJsonFile(speciesPath, speciesData)) {
        std::cerr << "[Learnset] Failed to save species.json" << std::endl;
        return false;
    }

    int totalMoves = 0;
    for (const auto& [k, v] : learnsets.items()) {
        totalMoves += v.size();
    }

    std::cout << "[Learnset] Done! " << learnsets.size() << " species, "
              << totalMoves << " total move entries ("
              << fetched << " fetched, " << skipped << " skipped)" << std::endl;

    return true;
}
