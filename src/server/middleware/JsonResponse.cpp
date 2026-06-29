#include "server/middleware/JsonResponse.h"

namespace server {
namespace middleware {

nlohmann::json JsonResponse::ok(const nlohmann::json& data) {
    nlohmann::json response;
    response["ok"] = true;
    response["data"] = data;
    response["error"] = nullptr;
    return response;
}

nlohmann::json JsonResponse::error(const std::string& message) {
    nlohmann::json response;
    response["ok"] = false;
    response["data"] = nullptr;
    response["error"] = message;
    return response;
}

nlohmann::json JsonResponse::paginated(const nlohmann::json& items, int page, int limit, int total) {
    nlohmann::json response;
    response["ok"] = true;
    response["data"] = items;
    response["error"] = nullptr;
    response["meta"]["page"] = page;
    response["meta"]["limit"] = limit;
    response["meta"]["total"] = total;
    return response;
}

std::string JsonResponse::okString(const nlohmann::json& data) {
    return ok(data).dump();
}

std::string JsonResponse::errorString(const std::string& message) {
    return error(message).dump();
}

} // namespace middleware
} // namespace server
