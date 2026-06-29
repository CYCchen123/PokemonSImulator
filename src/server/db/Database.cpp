#include "server/db/Database.h"

#include <cstring>
#include <fstream>
#include <sstream>
#include <iostream>

namespace server {
namespace db {

// ==========================================
// Static callback helpers
// ==========================================

namespace {

// Callback for queryToJson: builds a JSON array of objects
struct JsonQueryContext {
    nlohmann::json result = nlohmann::json::array();
};

int jsonQueryCallback(void* data, int argc, char** argv, char** colNames) {
    auto* ctx = static_cast<JsonQueryContext*>(data);
    nlohmann::json row = nlohmann::json::object();
    for (int i = 0; i < argc; i++) {
        row[colNames[i]] = argv[i] ? argv[i] : "";
    }
    ctx->result.push_back(std::move(row));
    return 0;
}

// Callback for general RowCallback
struct RowCallbackContext {
    Database::RowCallback callback;
    bool ok = true;
};

int rowCallbackBridge(void* data, int argc, char** argv, char** colNames) {
    auto* ctx = static_cast<RowCallbackContext*>(data);
    if (!ctx->callback(argc, argv, colNames)) {
        ctx->ok = false;
        return 1; // abort
    }
    return 0;
}

// Callback for executeAndCount
int countCallback(void* data, int /*argc*/, char** /*argv*/, char** /*colNames*/) {
    int* count = static_cast<int*>(data);
    (*count)++;
    return 0;
}

} // anonymous namespace

// ==========================================
// Database singleton
// ==========================================

Database& Database::instance() {
    static Database db;
    return db;
}

Database::~Database() {
    close();
}

bool Database::open(const std::string& path) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (db_) {
        return true; // already open
    }

    int rc = sqlite3_open(path.c_str(), &db_);
    if (rc != SQLITE_OK) {
        std::cerr << "[Database] Failed to open: " << sqlite3_errmsg(db_) << std::endl;
        sqlite3_close(db_);
        db_ = nullptr;
        return false;
    }

    // Enable WAL mode for better concurrent read performance
    execute("PRAGMA journal_mode=WAL;");
    execute("PRAGMA foreign_keys=ON;");

    path_ = path;
    std::cout << "[Database] Opened: " << path << std::endl;

    // Run migrations
    if (!runMigrations()) {
        std::cerr << "[Database] Migration failed" << std::endl;
        return false;
    }

    return true;
}

void Database::close() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (db_) {
        sqlite3_close(db_);
        db_ = nullptr;
        std::cout << "[Database] Closed" << std::endl;
    }
}

bool Database::isOpen() const {
    return db_ != nullptr;
}

bool Database::execute(const std::string& sql) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!db_) return false;

    char* errMsg = nullptr;
    int rc = sqlite3_exec(db_, sql.c_str(), nullptr, nullptr, &errMsg);
    if (rc != SQLITE_OK) {
        std::cerr << "[Database] SQL error: " << (errMsg ? errMsg : "unknown")
                  << "\n  SQL: " << sql.substr(0, 200) << std::endl;
        sqlite3_free(errMsg);
        return false;
    }
    return true;
}

int Database::executeAndCount(const std::string& sql) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!db_) return -1;

    int count = 0;
    char* errMsg = nullptr;
    int rc = sqlite3_exec(db_, sql.c_str(), countCallback, &count, &errMsg);
    if (rc != SQLITE_OK) {
        std::cerr << "[Database] SQL error: " << (errMsg ? errMsg : "unknown")
                  << "\n  SQL: " << sql.substr(0, 200) << std::endl;
        sqlite3_free(errMsg);
        return -1;
    }
    return count;
}

bool Database::query(const std::string& sql, RowCallback callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!db_) return false;

    RowCallbackContext ctx;
    ctx.callback = std::move(callback);

    char* errMsg = nullptr;
    int rc = sqlite3_exec(db_, sql.c_str(), rowCallbackBridge, &ctx, &errMsg);
    if (rc != SQLITE_OK) {
        std::cerr << "[Database] Query error: " << (errMsg ? errMsg : "unknown")
                  << "\n  SQL: " << sql.substr(0, 200) << std::endl;
        sqlite3_free(errMsg);
        return false;
    }
    return ctx.ok;
}

nlohmann::json Database::queryToJson(const std::string& sql) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!db_) return nlohmann::json::array();

    JsonQueryContext ctx;
    char* errMsg = nullptr;
    int rc = sqlite3_exec(db_, sql.c_str(), jsonQueryCallback, &ctx, &errMsg);
    if (rc != SQLITE_OK) {
        std::cerr << "[Database] Query error: " << (errMsg ? errMsg : "unknown")
                  << "\n  SQL: " << sql.substr(0, 200) << std::endl;
        sqlite3_free(errMsg);
        return nlohmann::json::array();
    }
    return ctx.result;
}

int64_t Database::lastInsertRowId() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!db_) return -1;
    return sqlite3_last_insert_rowid(db_);
}

bool Database::beginTransaction() {
    return execute("BEGIN TRANSACTION;");
}

bool Database::commitTransaction() {
    return execute("COMMIT;");
}

bool Database::rollbackTransaction() {
    return execute("ROLLBACK;");
}

bool Database::executeMigration(const std::string& sql) {
    return execute(sql);
}

int Database::getSchemaVersion() {
    // Check if schema_version table exists
    auto result = queryToJson(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version';");
    if (result.empty()) {
        return 0;
    }

    auto rows = queryToJson("SELECT MAX(version) as version FROM schema_version;");
    if (rows.empty() || !rows[0].contains("version")) {
        return 0;
    }
    const auto& v = rows[0]["version"];
    if (v.is_null()) return 0;
    if (v.is_string()) return std::stoi(v.get<std::string>());
    return v.get<int>();
}

bool Database::runMigrations() {
    int currentVersion = getSchemaVersion();
    std::cout << "[Database] Current schema version: " << currentVersion << std::endl;

    // Run migration 001 if needed
    if (currentVersion < 1) {
        std::cout << "[Database] Running migration 001..." << std::endl;

        // Read migration file
        // Try multiple paths relative to the working directory
        std::vector<std::string> searchPaths = {
            "src/server/db/migrations/001_initial.sql",
            "../src/server/db/migrations/001_initial.sql",
            "../../src/server/db/migrations/001_initial.sql",
        };

        std::string migrationSql;
        for (const auto& p : searchPaths) {
            std::ifstream f(p);
            if (f.is_open()) {
                std::stringstream buffer;
                buffer << f.rdbuf();
                migrationSql = buffer.str();
                std::cout << "[Database] Found migration at: " << p << std::endl;
                break;
            }
        }

        if (migrationSql.empty()) {
            std::cerr << "[Database] Could not find migration file 001_initial.sql" << std::endl;
            return false;
        }

        // Execute the entire migration as one statement batch
        // sqlite3_exec can handle multiple statements separated by ;
        char* errMsg = nullptr;
        int rc = sqlite3_exec(db_, migrationSql.c_str(), nullptr, nullptr, &errMsg);
        if (rc != SQLITE_OK) {
            std::cerr << "[Database] Migration 001 failed: "
                      << (errMsg ? errMsg : "unknown") << std::endl;
            sqlite3_free(errMsg);
            return false;
        }
        std::cout << "[Database] Migration 001 complete" << std::endl;
    }

    return true;
}

} // namespace db
} // namespace server
