#pragma once

#include <sqlite3.h>
#include <string>
#include <functional>
#include <mutex>
#include <vector>
#include <nlohmann/json.hpp>

namespace server {
namespace db {

/**
 * RAII wrapper around SQLite3 connection.
 * Thread-safe: all operations are protected by a mutex.
 */
class Database {
public:
    static Database& instance();

    // Disable copy
    Database(const Database&) = delete;
    Database& operator=(const Database&) = delete;

    /**
     * Open (or create) the database at the given path.
     * Runs pending migrations on first open.
     * Returns true on success.
     */
    bool open(const std::string& path);

    /** Close the database connection. */
    void close();

    /** Returns true if the database is open. */
    bool isOpen() const;

    /** Get raw sqlite3 handle (for advanced queries). Caller must hold mutex externally. */
    sqlite3* get() { return db_; }

    /** Execute a SQL statement (INSERT/UPDATE/DELETE/CREATE). Returns true on success. */
    bool execute(const std::string& sql);

    /** Execute a SQL statement and return the number of rows changed. */
    int executeAndCount(const std::string& sql);

    /**
     * Execute a SELECT query and invoke the callback for each row.
     * callback receives: (column count, column values array, column names array).
     * Returns true on success.
     */
    using RowCallback = std::function<bool(int argc, char** argv, char** colNames)>;
    bool query(const std::string& sql, RowCallback callback);

    /**
     * Execute a SELECT query and return all rows as a JSON array of objects.
     */
    nlohmann::json queryToJson(const std::string& sql);

    /** Get the last inserted row ID. */
    int64_t lastInsertRowId();

    /** Begin/commit/rollback transaction. */
    bool beginTransaction();
    bool commitTransaction();
    bool rollbackTransaction();

    /**
     * Run a migration SQL string. Used internally by runMigrations().
     */
    bool executeMigration(const std::string& sql);

    /** Get the current schema version. */
    int getSchemaVersion();

    /** Get the database file path. */
    const std::string& getPath() const { return path_; }

private:
    Database() = default;
    ~Database();

    bool runMigrations();

    sqlite3* db_ = nullptr;
    std::string path_;
    std::mutex mutex_;
};

} // namespace db
} // namespace server
