#include "server/HttpServer.h"
#include "server/db/Database.h"
#include "server/db/repositories/DataRepo.h"
#include "server/middleware/JsonResponse.h"

#include <iostream>
#include <nlohmann/json.hpp>

#define CPPHTTPLIB_OPENSSL_SUPPORT 0
#include "httplib.h"

namespace server {

// ==========================================
// Forward declarations of route handlers
// ==========================================
namespace handlers {
    void setupHealthRoutes(httplib::Server& svr);
    void setupDataRoutes(httplib::Server& svr);
    void setupPlayerRoutes(httplib::Server& svr);
    void setupTeamRoutes(httplib::Server& svr);
    void setupBattleRoutes(httplib::Server& svr);
    void setupStatsRoutes(httplib::Server& svr);
}

// ==========================================
// CORS middleware
// ==========================================
namespace {

void addCorsHeaders(httplib::Response& res) {
    res.set_header("Access-Control-Allow-Origin", "*");
    res.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
    res.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization");
    res.set_header("Access-Control-Max-Age", "86400");
}

} // anonymous namespace

// ==========================================
// Server startup
// ==========================================

bool startServer(int port, const std::string& dbPath) {
    // Open database
    auto& db = db::Database::instance();
    if (!db.open(dbPath)) {
        std::cerr << "[Server] Failed to open database: " << dbPath << std::endl;
        return false;
    }

    // Seed static data if needed
    std::cout << "[Server] Checking static data..." << std::endl;
    if (!db::DataRepo::seedAllIfEmpty()) {
        std::cerr << "[Server] Warning: failed to seed some static data tables" << std::endl;
        // Continue anyway - some data is better than none
    }

    // Create HTTP server
    httplib::Server svr;

    // CORS preflight handler
    svr.Options(R"(.*)", [](const httplib::Request&, httplib::Response& res) {
        addCorsHeaders(res);
        res.set_content("", "text/plain");
    });

    // Setup all route groups
    handlers::setupHealthRoutes(svr);
    handlers::setupDataRoutes(svr);
    handlers::setupPlayerRoutes(svr);
    handlers::setupTeamRoutes(svr);
    handlers::setupBattleRoutes(svr);
    handlers::setupStatsRoutes(svr);

    // Static file serving for Vue production build (if frontend/dist/ exists)
    svr.set_mount_point("/", "frontend/dist/");

    // Start listening
    std::cout << "[Server] Starting HTTP server on port " << port << "..." << std::endl;
    std::cout << "[Server] API base URL: http://localhost:" << port << "/api/v1" << std::endl;
    std::cout << "[Server] Press Ctrl+C to stop" << std::endl;

    if (!svr.listen("0.0.0.0", port)) {
        std::cerr << "[Server] Failed to start server on port " << port << std::endl;
        return false;
    }

    return true;
}

// ==========================================
// Route handler implementations
// ==========================================
namespace handlers {

void setupHealthRoutes(httplib::Server& svr) {
    svr.Get("/api/v1/health", [](const httplib::Request& req, httplib::Response& res) {
        addCorsHeaders(res);
        auto& db = db::Database::instance();
        nlohmann::json status;
        status["status"] = "healthy";
        status["database"] = db.isOpen() ? "connected" : "disconnected";
        status["db_path"] = db.getPath();
        status["schema_version"] = db.getSchemaVersion();
        res.set_content(middleware::JsonResponse::okString(status), "application/json");
    });
}

void setupDataRoutes(httplib::Server& svr) {
    auto& db = db::Database::instance();

    // GET /api/v1/data/enums
    svr.Get("/api/v1/data/enums", [](const httplib::Request&, httplib::Response& res) {
        addCorsHeaders(res);
        auto enums = db::DataRepo::getEnumMappings();
        res.set_content(middleware::JsonResponse::okString(enums), "application/json");
    });

    // GET /api/v1/data/species
    svr.Get("/api/v1/data/species", [&db](const httplib::Request& req, httplib::Response& res) {
        addCorsHeaders(res);

        std::string sql = "SELECT id, name, type1, type2, base_hp, base_atk, base_def, "
                          "base_spa, base_spd, base_spe FROM species WHERE 1=1";

        if (req.has_param("name")) {
            sql += " AND name LIKE '%" + req.get_param_value("name") + "%'";
        }
        if (req.has_param("type")) {
            std::string t = req.get_param_value("type");
            sql += " AND (type1='" + t + "' OR type2='" + t + "')";
        }

        int limit = 50;
        if (req.has_param("limit")) {
            limit = std::stoi(req.get_param_value("limit"));
        }
        sql += " LIMIT " + std::to_string(limit);

        auto data = db.queryToJson(sql);
        res.set_content(middleware::JsonResponse::okString(data), "application/json");
    });

    // GET /api/v1/data/species/{id}
    svr.Get(R"(/api/v1/data/species/(\d+))", [&db](const httplib::Request& req, httplib::Response& res) {
        addCorsHeaders(res);
        int id = std::stoi(req.matches[1]);
        auto data = db.queryToJson(
            "SELECT * FROM species WHERE id=" + std::to_string(id) + ";");
        if (data.empty()) {
            res.status = 404;
            res.set_content(middleware::JsonResponse::errorString("Species not found"), "application/json");
            return;
        }
        res.set_content(middleware::JsonResponse::okString(data[0]), "application/json");
    });

    // GET /api/v1/data/moves
    svr.Get("/api/v1/data/moves", [&db](const httplib::Request& req, httplib::Response& res) {
        addCorsHeaders(res);

        std::string sql = "SELECT id, name, type, category, power, accuracy, pp, priority, "
                          "target, effect, effect_chance FROM moves WHERE 1=1";

        if (req.has_param("name")) {
            sql += " AND name LIKE '%" + req.get_param_value("name") + "%'";
        }
        if (req.has_param("type")) {
            sql += " AND type='" + req.get_param_value("type") + "'";
        }
        if (req.has_param("category")) {
            sql += " AND category='" + req.get_param_value("category") + "'";
        }

        int limit = 50;
        if (req.has_param("limit")) {
            limit = std::stoi(req.get_param_value("limit"));
        }
        sql += " ORDER BY id LIMIT " + std::to_string(limit);

        auto data = db.queryToJson(sql);
        res.set_content(middleware::JsonResponse::okString(data), "application/json");
    });

    // GET /api/v1/data/moves/{id}
    svr.Get(R"(/api/v1/data/moves/(\d+))", [&db](const httplib::Request& req, httplib::Response& res) {
        addCorsHeaders(res);
        int id = std::stoi(req.matches[1]);
        auto data = db.queryToJson(
            "SELECT * FROM moves WHERE id=" + std::to_string(id) + ";");
        if (data.empty()) {
            res.status = 404;
            res.set_content(middleware::JsonResponse::errorString("Move not found"), "application/json");
            return;
        }
        res.set_content(middleware::JsonResponse::okString(data[0]), "application/json");
    });

    // GET /api/v1/data/abilities
    svr.Get("/api/v1/data/abilities", [&db](const httplib::Request& req, httplib::Response& res) {
        addCorsHeaders(res);

        std::string sql = "SELECT id, name FROM abilities WHERE 1=1";

        if (req.has_param("name")) {
            sql += " AND name LIKE '%" + req.get_param_value("name") + "%'";
        }

        int limit = 50;
        if (req.has_param("limit")) {
            limit = std::stoi(req.get_param_value("limit"));
        }
        sql += " ORDER BY id LIMIT " + std::to_string(limit);

        auto data = db.queryToJson(sql);
        res.set_content(middleware::JsonResponse::okString(data), "application/json");
    });

    // GET /api/v1/data/abilities/{id}
    svr.Get(R"(/api/v1/data/abilities/(\d+))", [&db](const httplib::Request& req, httplib::Response& res) {
        addCorsHeaders(res);
        int id = std::stoi(req.matches[1]);
        auto data = db.queryToJson(
            "SELECT * FROM abilities WHERE id=" + std::to_string(id) + ";");
        if (data.empty()) {
            res.status = 404;
            res.set_content(middleware::JsonResponse::errorString("Ability not found"), "application/json");
            return;
        }
        res.set_content(middleware::JsonResponse::okString(data[0]), "application/json");
    });

    // GET /api/v1/data/items
    svr.Get("/api/v1/data/items", [&db](const httplib::Request& req, httplib::Response& res) {
        addCorsHeaders(res);

        std::string sql = "SELECT id, name, is_battle FROM items WHERE 1=1";

        if (req.has_param("name")) {
            sql += " AND name LIKE '%" + req.get_param_value("name") + "%'";
        }

        int limit = 50;
        if (req.has_param("limit")) {
            limit = std::stoi(req.get_param_value("limit"));
        }
        sql += " ORDER BY id LIMIT " + std::to_string(limit);

        auto data = db.queryToJson(sql);
        res.set_content(middleware::JsonResponse::okString(data), "application/json");
    });

    // GET /api/v1/data/items/{id}
    svr.Get(R"(/api/v1/data/items/(\d+))", [&db](const httplib::Request& req, httplib::Response& res) {
        addCorsHeaders(res);
        int id = std::stoi(req.matches[1]);
        auto data = db.queryToJson(
            "SELECT * FROM items WHERE id=" + std::to_string(id) + ";");
        if (data.empty()) {
            res.status = 404;
            res.set_content(middleware::JsonResponse::errorString("Item not found"), "application/json");
            return;
        }
        res.set_content(middleware::JsonResponse::okString(data[0]), "application/json");
    });
}

// ==========================================
// Stub handlers (to be implemented in later phases)
// ==========================================

void setupPlayerRoutes(httplib::Server& svr) {
    auto& db = db::Database::instance();

    svr.Get("/api/v1/players", [&db](const httplib::Request&, httplib::Response& res) {
        addCorsHeaders(res);
        auto data = db.queryToJson("SELECT * FROM players ORDER BY id;");
        res.set_content(middleware::JsonResponse::okString(data), "application/json");
    });

    svr.Get(R"(/api/v1/players/(\d+))", [&db](const httplib::Request& req, httplib::Response& res) {
        addCorsHeaders(res);
        int id = std::stoi(req.matches[1]);
        auto data = db.queryToJson("SELECT * FROM players WHERE id=" + std::to_string(id) + ";");
        if (data.empty()) {
            res.status = 404;
            res.set_content(middleware::JsonResponse::errorString("Player not found"), "application/json");
            return;
        }
        res.set_content(middleware::JsonResponse::okString(data[0]), "application/json");
    });

    svr.Post("/api/v1/players", [&db](const httplib::Request& req, httplib::Response& res) {
        addCorsHeaders(res);
        auto body = nlohmann::json::parse(req.body, nullptr, false);
        if (body.is_discarded() || !body.contains("name")) {
            res.status = 400;
            res.set_content(middleware::JsonResponse::errorString("Missing 'name' field"), "application/json");
            return;
        }
        std::string name = body["name"].get<std::string>();
        // Escape single quotes
        std::string escaped;
        for (char c : name) {
            if (c == '\'') escaped += "''";
            else escaped += c;
        }
        db.execute("INSERT INTO players (name) VALUES ('" + escaped + "');");
        int64_t playerId = db.lastInsertRowId();
        auto data = db.queryToJson("SELECT * FROM players WHERE id=" + std::to_string(playerId) + ";");
        res.status = 201;
        res.set_content(middleware::JsonResponse::okString(data.empty() ? nlohmann::json::object() : data[0]), "application/json");
    });
}

void setupTeamRoutes(httplib::Server& svr) {
    auto& db = db::Database::instance();

    svr.Get("/api/v1/teams", [&db](const httplib::Request& req, httplib::Response& res) {
        addCorsHeaders(res);
        std::string sql = "SELECT id, player_id, name, created_at, updated_at FROM teams";
        if (req.has_param("player_id")) {
            sql += " WHERE player_id=" + req.get_param_value("player_id");
        }
        sql += " ORDER BY id DESC LIMIT 50;";
        auto data = db.queryToJson(sql);
        res.set_content(middleware::JsonResponse::okString(data), "application/json");
    });

    svr.Get(R"(/api/v1/teams/(\d+))", [&db](const httplib::Request& req, httplib::Response& res) {
        addCorsHeaders(res);
        int id = std::stoi(req.matches[1]);
        auto data = db.queryToJson("SELECT * FROM teams WHERE id=" + std::to_string(id) + ";");
        if (data.empty()) {
            res.status = 404;
            res.set_content(middleware::JsonResponse::errorString("Team not found"), "application/json");
            return;
        }
        res.set_content(middleware::JsonResponse::okString(data[0]), "application/json");
    });

    svr.Post("/api/v1/teams", [&db](const httplib::Request& req, httplib::Response& res) {
        addCorsHeaders(res);
        auto body = nlohmann::json::parse(req.body, nullptr, false);
        if (body.is_discarded() || !body.contains("player_id") || !body.contains("pokemon")) {
            res.status = 400;
            res.set_content(middleware::JsonResponse::errorString("Missing required fields: player_id, pokemon"), "application/json");
            return;
        }
        int playerId = body["player_id"].get<int>();
        std::string name = body.value("name", "Untitled Team");
        std::string teamJson = body.dump();

        // Escape
        std::string escapedName;
        for (char c : name) { if (c == '\'') escapedName += "''"; else escapedName += c; }
        std::string escapedJson;
        for (char c : teamJson) { if (c == '\'') escapedJson += "''"; else escapedJson += c; }

        db.execute(
            "INSERT INTO teams (player_id, name, team_json) VALUES (" +
            std::to_string(playerId) + ", '" + escapedName + "', '" + escapedJson + "');");
        int64_t teamId = db.lastInsertRowId();
        auto data = db.queryToJson("SELECT * FROM teams WHERE id=" + std::to_string(teamId) + ";");
        res.status = 201;
        res.set_content(middleware::JsonResponse::okString(data.empty() ? nlohmann::json::object() : data[0]), "application/json");
    });

    svr.Delete(R"(/api/v1/teams/(\d+))", [&db](const httplib::Request& req, httplib::Response& res) {
        addCorsHeaders(res);
        int id = std::stoi(req.matches[1]);
        db.execute("DELETE FROM teams WHERE id=" + std::to_string(id) + ";");
        res.set_content(middleware::JsonResponse::okString({{"deleted", id}}), "application/json");
    });
}

void setupBattleRoutes(httplib::Server& svr) {
    auto& db = db::Database::instance();

    svr.Get("/api/v1/battles", [&db](const httplib::Request& req, httplib::Response& res) {
        addCorsHeaders(res);
        std::string sql = "SELECT id, player_a_id, player_b_id, winner_side, total_turns, status, created_at FROM battles";
        if (req.has_param("status")) {
            sql += " WHERE status='" + req.get_param_value("status") + "'";
        }
        sql += " ORDER BY id DESC LIMIT 50;";
        auto data = db.queryToJson(sql);
        res.set_content(middleware::JsonResponse::okString(data), "application/json");
    });

    svr.Get(R"(/api/v1/battles/(\d+))", [&db](const httplib::Request& req, httplib::Response& res) {
        addCorsHeaders(res);
        int id = std::stoi(req.matches[1]);
        auto data = db.queryToJson("SELECT * FROM battles WHERE id=" + std::to_string(id) + ";");
        if (data.empty()) {
            res.status = 404;
            res.set_content(middleware::JsonResponse::errorString("Battle not found"), "application/json");
            return;
        }
        res.set_content(middleware::JsonResponse::okString(data[0]), "application/json");
    });
}

void setupStatsRoutes(httplib::Server& svr) {
    auto& db = db::Database::instance();

    svr.Get("/api/v1/stats/global", [&db](const httplib::Request&, httplib::Response& res) {
        addCorsHeaders(res);
        nlohmann::json stats;
        auto battleCount = db.queryToJson("SELECT COUNT(*) as total FROM battles;");
        stats["total_battles"] = battleCount.empty() ? 0 : battleCount[0]["total"];
        auto playerCount = db.queryToJson("SELECT COUNT(*) as total FROM players;");
        stats["total_players"] = playerCount.empty() ? 0 : playerCount[0]["total"];
        auto teamCount = db.queryToJson("SELECT COUNT(*) as total FROM teams;");
        stats["total_teams"] = teamCount.empty() ? 0 : teamCount[0]["total"];
        res.set_content(middleware::JsonResponse::okString(stats), "application/json");
    });
}

} // namespace handlers
} // namespace server
