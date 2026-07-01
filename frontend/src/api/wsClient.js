/**
 * WebSocket client for PokemonSimulator.
 * Singleton connection with message routing via type-based callbacks.
 */
const WS_URL = `ws://${location.hostname}:${location.port}/ws`

let ws = null
let playerId = null
let reconnectTimer = null
const handlers = new Map()   // type → Set<callback>
const pending = new Map()    // request id → resolve
let msgId = 0

export function getPlayerId() { return playerId }

export function connect(playerName = 'Trainer') {
  const expectedId = localStorage.getItem('trainer_name') || playerName.replace(/\s+/g,'_')
  // If WS open but playerId doesn't match expected, reconnect
  if (ws && ws.readyState === WebSocket.OPEN) {
    if (playerId === expectedId) return Promise.resolve(playerId)
    // Name changed - close old and reconnect
    ws.close()
    ws = null
  }

  // If already connecting, wait for it instead of creating a duplicate
  if (ws && ws.readyState === WebSocket.CONNECTING) {
    return new Promise((resolve, reject) => {
      const check = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN && playerId) {
          clearInterval(check); resolve(playerId)
        }
      }, 100)
      setTimeout(() => { clearInterval(check); reject(new Error('connect timeout')) }, 10000)
    })
  }

  return new Promise((resolve, reject) => {
    ws = new WebSocket(WS_URL)

    ws.onopen = () => {
      // Use trainer name as persistent ID
      playerId = localStorage.getItem('trainer_name') || playerName.replace(/\s+/g,'_')
      sendRaw({ type: 'handshake', data: { player_id: playerId } })
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        const { type, data, id } = msg

        // Resolve pending request
        if (id && pending.has(id)) {
          pending.get(id)(data)
          pending.delete(id)
          return
        }

        // Dispatch to type handlers
        if (handlers.has(type)) {
          handlers.get(type).forEach(fn => fn(data))
        }
        // Also dispatch to wildcard
        if (handlers.has('*')) {
          handlers.get('*').forEach(fn => fn(type, data))
        }
      } catch (e) {
        console.error('[WS] parse error:', e)
      }
    }

    ws.onclose = () => {
      console.log('[WS] disconnected');
      // Auto reconnect
      reconnectTimer = setTimeout(() => connect(playerName), 2000)
    }

    ws.onerror = (e) => {
      console.error('[WS] error:', e)
      reject(e)
    }

    // Wait for handshake
    const check = setInterval(() => {
      if (playerId) {
        clearInterval(check)
        resolve(playerId)
      }
    }, 100)
    setTimeout(() => { clearInterval(check); reject(new Error('handshake timeout')) }, 5000)
  })
}

function sendRaw(msg) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(msg))
  }
}

/** Send a message and get a Promise for the response (request/response pattern) */
export function request(type, data = {}) {
  const id = String(++msgId)
  return new Promise((resolve, reject) => {
    pending.set(id, resolve)
    sendRaw({ type, data, id })
    setTimeout(() => {
      if (pending.has(id)) {
        pending.delete(id)
        reject(new Error(`Request timeout: ${type}`))
      }
    }, 15000)
  })
}

/** Send a fire-and-forget message */
export function send(type, data = {}) {
  sendRaw({ type, data })
}

/** Subscribe to a message type */
export function on(type, callback) {
  if (!handlers.has(type)) handlers.set(type, new Set())
  handlers.get(type).add(callback)
  return () => handlers.get(type)?.delete(callback)  // return unsubscribe
}

/** One-time subscription */
export function once(type, callback) {
  const unsub = on(type, (data) => {
    callback(data)
    unsub()
  })
}

export function disconnect() {
  clearTimeout(reconnectTimer)
  if (ws) ws.close()
  ws = null
  playerId = null
}
