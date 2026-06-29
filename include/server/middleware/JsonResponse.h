#pragma once

#include <string>
#include <nlohmann/json.hpp>

namespace server {
namespace middleware {

/**
 * Build a standard API response envelope:
 *   { "ok": true/false, "data": ..., "error": "..." }
 */
class JsonResponse {
public:
    /** Success response with data. */
    static nlohmann::json ok(const nlohmann::json& data = nlohmann::json::object());

    /** Error response with message. */
    static nlohmann::json error(const std::string& message);

    /** Paginated list response. */
    static nlohmann::json paginated(const nlohmann::json& items, int page, int limit, int total);

    /** Success response as string (for HTTP body). */
    static std::string okString(const nlohmann::json& data = nlohmann::json::object());

    /** Error response as string. */
    static std::string errorString(const std::string& message);
};

} // namespace middleware
} // namespace server
