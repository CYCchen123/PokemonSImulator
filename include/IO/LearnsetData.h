#pragma once

#include <string>

/**
 * Prefetch learnable moves from PokeAPI for all species.
 * Calls PokeAPI /api/v2/pokemon/{id} for each species and extracts move IDs.
 * Writes to data/learnsets.json and updates data/species.json with learnableMoves.
 *
 * @param refresh  If true, re-fetch even if learnsets.json already has data.
 * @return true on success.
 */
bool prefetchLearnsetsFromPokeAPI(bool refresh);
