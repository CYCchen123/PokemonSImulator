#pragma once

#include <string>
#include <cstdint>

namespace server {

/**
 * Start the HTTP server on the given port.
 * Blocking call - runs the event loop until the server is stopped.
 * @param port TCP port to listen on (default 8080)
 * @param dbPath Path to the SQLite database file
 * @return true if server started and ran successfully
 */
bool startServer(int port = 8080, const std::string& dbPath = "data/pokemon_simulator.db");

} // namespace server
