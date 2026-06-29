#pragma once

#include <string>
#include <nlohmann/json.hpp>

namespace server {
namespace db {

/**
 * Repository for static game data (species, moves, abilities, items).
 * Loads from data/*.json files into SQLite on first run.
 */
class DataRepo {
public:
    /**
     * Seed all static data tables from data/*.json files.
     * Idempotent: skips tables that already have data.
     * Returns true on success.
     */
    static bool seedAllIfEmpty();

    /** Seed species table from data/species.json */
    static bool seedSpecies();

    /** Seed moves table from data/moves.json */
    static bool seedMoves();

    /** Seed abilities table from data/abilities.json */
    static bool seedAbilities();

    /** Seed items table from data/items.json */
    static bool seedItems();

    /** Check if a table has data */
    static bool tableHasData(const std::string& tableName);

    /** Resolve a file path by trying multiple search locations */
    static std::string resolveDataPath(const std::string& filename);

    /** Get all enum value-to-name mappings for the frontend */
    static nlohmann::json getEnumMappings();
};

} // namespace db
} // namespace server
