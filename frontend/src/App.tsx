import React, { useEffect, useMemo, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

type Player = {
  name: string
  stack: number
  position: string
  current_bet: number
  hole_cards?: string[]
}

type GameState = {
  hand_number: number
  dealer_position: number
  dealer_name?: string
  street: string | null
  pot: number
  current_bet: number
  community_cards: string[]
  players: Player[]
  awaiting_player: string | null
  is_complete: boolean
  action_log?: string[]
  winners?: string[]
  hands?: Record<string, { hole_cards: string[] }>
  legal_actions?: {
    fold?: boolean
    check?: boolean
    call?: boolean
    raise?: { allowed: boolean, min: number, max: number } | null
  }
}

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [sessionId, setSessionId] = useState<string>('')
  const [state, setState] = useState<GameState | null>(null)
  const [raiseTo, setRaiseTo] = useState<number>(0)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string>('')
  const [playerTimeLeft, setPlayerTimeLeft] = useState<number>(0)
  const [botTimeLeft, setBotTimeLeft] = useState<number>(0)
  const playerTimerRef = useRef<any>(null)
  const botTimerRef = useRef<any>(null)

  const start = async () => {
    setError('')
    setLoading(true)
    try {
      const res = await fetch(`${API}/start_game`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) })
      if (!res.ok) {
        const text = await res.text().catch(() => '')
        throw new Error(`Start failed (${res.status}): ${text}`)
      }
      const data = await res.json()
      setSessionId(data.session_id)
      setState(data.state)
    } catch (e: any) {
      console.error('Start game error', e)
      setError(e?.message || 'Failed to start game')
    } finally {
      setLoading(false)
    }
  }

  const refresh = async () => {
    if (!sessionId) return
    try {
      const res = await fetch(`${API}/state?session_id=${sessionId}`)
      if (!res.ok) return
      const data = await res.json()
      setState(data)
    } catch (e) {
      // ignore background errors
    }
  }

  const act = async (action: string, amount: number = 0) => {
    if (!sessionId) return
    try {
      const res = await fetch(`${API}/player_action`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId, action, amount }) })
      if (!res.ok) {
        const text = await res.text().catch(() => '')
        throw new Error(text || 'Action failed')
      }
      const data = await res.json()
      setState(data)
      setError('')
    } catch (e: any) {
      console.error('Player action error', e)
      setError(e?.message || 'Action failed')
    }
  }

  const botAct = async () => {
    if (!sessionId) return
    try {
      const res = await fetch(`${API}/bot_action?session_id=${sessionId}`)
      if (!res.ok) return
      const data = await res.json()
      setState(data)
    } catch (e) {}
  }

  const nextHand = async () => {
    if (!sessionId) return
    try {
      const res = await fetch(`${API}/next_hand`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId }) })
      if (!res.ok) throw new Error('Next hand failed')
      const data = await res.json()
      setState(data)
    } catch (e) {
      // keep UI stable
    }
  }

  useEffect(() => {
    const id = setInterval(() => {
      refresh()
    }, 1500)
    return () => clearInterval(id)
  }, [sessionId])

  // Turn timers and auto-actions
  useEffect(() => {
    if (playerTimerRef.current) { clearInterval(playerTimerRef.current); playerTimerRef.current = null }
    if (botTimerRef.current) { clearInterval(botTimerRef.current); botTimerRef.current = null }
    if (!state?.awaiting_player) return
    const humanName = 'You'
    if (state.awaiting_player === humanName) {
      const total = 10000
      const startAt = Date.now()
      setPlayerTimeLeft(total)
      playerTimerRef.current = setInterval(() => {
        const left = Math.max(0, total - (Date.now() - startAt))
        setPlayerTimeLeft(left)
        if (left <= 0) {
          clearInterval(playerTimerRef.current)
          playerTimerRef.current = null
          act('fold')
        }
      }, 100)
    } else {
      const total = 2000
      const startAt = Date.now()
      setBotTimeLeft(total)
      botTimerRef.current = setInterval(() => {
        const left = Math.max(0, total - (Date.now() - startAt))
        setBotTimeLeft(left)
        if (left <= 0) {
          clearInterval(botTimerRef.current)
          botTimerRef.current = null
          botAct()
        }
      }, 100)
    }
  }, [state?.awaiting_player])

  // Keep raise amount within current legal bounds and set sensible default
  useEffect(() => {
    if (!state?.legal_actions?.raise?.allowed) return
    const min = state.legal_actions.raise.min
    const max = state.legal_actions.raise.max
    // If current raiseTo is out of bounds or zero, default to min
    if (!raiseTo || raiseTo < min || raiseTo > max) {
      setRaiseTo(min)
    }
  }, [state?.legal_actions?.raise?.allowed, state?.legal_actions?.raise?.min, state?.legal_actions?.raise?.max])

  const clampRaise = (v: number) => {
    if (!state?.legal_actions?.raise?.allowed) return 0
    const min = state.legal_actions.raise.min
    const max = state.legal_actions.raise.max
    const nv = Math.max(min, Math.min(v, max))
    return nv
  }

  const setPercentOfPot = (pct: number) => {
    if (!state?.legal_actions?.raise?.allowed) return
    const max = state.legal_actions.raise.max
    const desired = Math.round(max * pct)
    setRaiseTo(clampRaise(desired))
  }

  const isPercentAllowed = (pct: number) => {
    if (!state?.legal_actions?.raise?.allowed) return false
    const { min, max } = state.legal_actions.raise
    const desired = Math.round(max * pct)
    return desired >= min
  }

  const Card = ({ value, faceDown = false, idx, shouldAnimate = false }: { value: string, faceDown?: boolean, idx?: number, shouldAnimate?: boolean }) => {
    const pattern = {
      backgroundImage: 'repeating-linear-gradient(45deg, rgba(255,255,255,0.15) 0, rgba(255,255,255,0.15) 4px, transparent 4px, transparent 8px)'
    } as React.CSSProperties
    return (
      <motion.div
        initial={shouldAnimate ? { opacity: 0, y: -10 } : false}
        animate={{ opacity: 1, y: 0 }}
        transition={shouldAnimate ? { delay: (idx || 0) * 0.05 } : undefined}
        className={`w-12 h-16 rounded-md border border-black shadow-sm flex items-center justify-center text-black select-none ${faceDown ? 'bg-red-700' : 'bg-white'}`}
        style={faceDown ? pattern : undefined}
      >
        {!faceDown && <span className="font-semibold">{value}</span>}
      </motion.div>
    )
  }

  const community = useMemo(() => {
    const cards = state?.community_cards || []
    const slots = Array.from({ length: 5 }, (_, i) => cards[i] || null)
    return slots
  }, [state?.community_cards])

  // Track prior dealt cards to animate only when a card first appears
  const prevCommunityRef = useRef<(string | null)[]>([null, null, null, null, null])
  const prevHumanRef = useRef<(string | null)[]>([null, null])
  useEffect(() => {
    prevCommunityRef.current = community
  }, [community])
  useEffect(() => {
    const hc = (state?.players.find(p => p.name === 'You')?.hole_cards || []).map(c => c || null)
    prevHumanRef.current = [hc[0] || null, hc[1] || null]
  }, [state?.players])

  const human = useMemo(() => state?.players.find(p => p.name === 'You'), [state?.players])
  const bot = useMemo(() => state?.players.find(p => p.name !== 'You'), [state?.players])
  const dealerName = state?.dealer_name

  return (
    <div className="min-h-screen bg-green-900 text-white p-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-4">Heads-Up Pot-Limit Poker</h1>
        {!sessionId && (
          <div className="space-y-2">
            <button className="bg-blue-600 px-4 py-2 rounded disabled:opacity-60" onClick={start} disabled={loading}>
              {loading ? 'Starting…' : 'Start Game'}
            </button>
            {error && <div className="text-red-300 text-sm">{error}</div>}
          </div>
        )}

        {state && (
          <div className="mt-4 space-y-4">
            {/* Poker Table */}
            <div className="relative mx-auto" style={{ width: 720, height: 480 }}>
              <div className="absolute inset-0 rounded-full bg-green-800/90 shadow-2xl border-4 border-green-700" />

              {/* Pot in center */}
              <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-center">
                <div className="text-sm opacity-90">Pot</div>
                <div className="text-2xl font-bold">{state.pot}</div>
              </div>

              {/* Community cards */}
              <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 mt-14 flex space-x-2">
                {community.map((c, i) => {
                  const prev = prevCommunityRef.current[i]
                  const shouldAnimate = !!c && !prev
                  return (
                    <Card key={i} value={c || ''} faceDown={!c} idx={i} shouldAnimate={shouldAnimate} />
                  )
                })}
              </div>

              {/* Top player (Computer) */}
              {bot && (
                <div className="absolute left-1/2 -translate-x-1/2 top-6 flex flex-col items-center">
                  <div className="mb-2 text-sm bg-black/30 px-2 py-1 rounded">Bet: {bot.current_bet}</div>
                  <div className="flex items-center space-x-2">
                    {state.dealer_name === bot.name && (
                      <div className="mr-2 w-6 h-6 rounded-full bg-yellow-300 text-black flex items-center justify-center text-xs font-bold">D</div>
                    )}
                    <AnimatePresence>
                      {Array.from({ length: 2 }).map((_, i) => (
                        <Card key={i} idx={i} value={state.is_complete && state.hands && state.hands[bot.name] ? state.hands[bot.name].hole_cards[i] : ''} faceDown={!(state.is_complete && state.hands && state.hands[bot.name])} />
                      ))}
                    </AnimatePresence>
                  </div>
                  {/* Bot timer bar (2s) */}
                  <div className="mt-2 w-40 h-2 bg-black/30 rounded overflow-hidden">
                    <div className="h-full bg-purple-400" style={{ width: `${Math.max(0, Math.min(100, 100 - (botTimeLeft/20)))}%` }} />
                  </div>
                  <div className="mt-2 text-sm">Stack: {bot.stack}</div>
                </div>
              )}

              {/* Bottom player (You) */}
              {human && (
                <div className="absolute left-1/2 -translate-x-1/2 bottom-6 flex flex-col items-center">
                  <div className="mb-2 text-sm bg-black/30 px-2 py-1 rounded">Bet: {human.current_bet}</div>
                  <div className="flex items-center space-x-2">
                    {state.dealer_name === human.name && (
                      <div className="mr-2 w-6 h-6 rounded-full bg-yellow-300 text-black flex items-center justify-center text-xs font-bold">D</div>
                    )}
                    <AnimatePresence>
                      {(human.hole_cards || ["", ""]).map((c, i) => {
                        const prev = prevHumanRef.current[i]
                        const shouldAnimate = !!c && !prev
                        return (
                          <Card key={i} idx={i} value={c || ''} faceDown={!c} shouldAnimate={shouldAnimate} />
                        )
                      })}
                    </AnimatePresence>
                  </div>
                  {/* Player timer bar (10s) */}
                  <div className="mt-2 w-40 h-2 bg-black/30 rounded overflow-hidden">
                    <div className="h-full bg-blue-400" style={{ width: `${Math.max(0, Math.min(100, (playerTimeLeft/100)))}%` }} />
                  </div>
                  <div className="mt-2 text-sm">Stack: {human.stack}</div>
                </div>
              )}
            </div>
            <div className="bg-green-800 p-4 rounded">
              <div>Hand: {state.hand_number}</div>
              <div>Dealer: {state.dealer_name || (state.dealer_position === 0 ? (state.players?.[0]?.name || 'P0') : (state.players?.[1]?.name || 'P1'))}</div>
              <div>Street: {state.street}</div>
              <div>Pot: {state.pot}</div>
              <div>Current Bet: {state.current_bet}</div>
              <div>Board: {state.community_cards.join(' ') || '—'}</div>
              <div>Awaiting: {state.awaiting_player || '—'}</div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {state.players.map((p) => (
                <div key={p.name} className="bg-green-800 p-4 rounded">
                  <div className="font-semibold">{p.name} ({p.position})</div>
                  <div>Stack: {p.stack}</div>
                  <div>Bet: {p.current_bet}</div>
                  <div className="mt-2">
                    Hole: {
                      // Show user's own cards always; bot's only at showdown
                      p.name === 'You'
                        ? ((p.hole_cards || []).join(' ') || '?? ??')
                        : (state.is_complete && state.hands && state.hands[p.name]
                            ? (state.hands[p.name].hole_cards || []).join(' ')
                            : '?? ??')
                    }
                  </div>
                </div>
              ))}
            </div>

            <div className="fixed bottom-4 right-4 bg-green-800 p-4 rounded space-x-2 flex items-center shadow-lg border border-green-700">
              {state.legal_actions?.raise?.allowed ? (
                <div className="flex items-center space-x-2 mr-4">
                  <button
                    className={`bg-gray-700 px-3 py-1 rounded text-sm ${!isPercentAllowed(0.33) ? 'opacity-50 cursor-not-allowed' : ''}`}
                    onClick={() => isPercentAllowed(0.33) && setPercentOfPot(0.33)}
                    disabled={!isPercentAllowed(0.33)}
                  >
                    33%
                  </button>
                  <button
                    className={`bg-gray-700 px-3 py-1 rounded text-sm ${!isPercentAllowed(0.5) ? 'opacity-50 cursor-not-allowed' : ''}`}
                    onClick={() => isPercentAllowed(0.5) && setPercentOfPot(0.5)}
                    disabled={!isPercentAllowed(0.5)}
                  >
                    50%
                  </button>
                  <button
                    className={`bg-gray-700 px-3 py-1 rounded text-sm ${!isPercentAllowed(1) ? 'opacity-50 cursor-not-allowed' : ''}`}
                    onClick={() => isPercentAllowed(1) && setPercentOfPot(1)}
                    disabled={!isPercentAllowed(1)}
                  >
                    100%
                  </button>
                  <div className="flex items-center space-x-2 ml-2">
                    <div className="bg-white text-black px-3 py-1 rounded">{raiseTo || 0}</div>
                    <input
                      type="range"
                      className="w-40"
                      min={state.legal_actions.raise.min}
                      max={state.legal_actions.raise.max}
                      step={1}
                      value={raiseTo}
                      onChange={(e) => setRaiseTo(clampRaise(parseInt(e.target.value || '0')))}
                    />
                  </div>
                </div>
              ) : null}
              {state.legal_actions?.fold ? (
                <button className="bg-red-600 px-3 py-2 rounded" onClick={() => act('fold')}>Fold</button>
              ) : null}
              {state.legal_actions?.check ? (
                <button className="bg-gray-600 px-3 py-2 rounded" onClick={() => act('check')}>Check</button>
              ) : null}
              {state.legal_actions?.call ? (
                <button className="bg-yellow-600 px-3 py-2 rounded" onClick={() => act('call', state.current_bet)}>Call</button>
              ) : null}
              {state.legal_actions?.raise?.allowed ? (
                <button
                  className="bg-blue-600 px-3 py-2 rounded"
                  onClick={() => act('raise', clampRaise(raiseTo || 0))}
                >
                  Raise
                </button>
              ) : null}
              {/* Removed Bot Act button */}
              {error && <div className="text-red-300 text-sm ml-3">{error}</div>}
            </div>

            {state.is_complete && (
              <div className="bg-green-800 p-4 rounded flex items-center space-x-3 mt-4">
                <div>
                  Hand complete{state.winners ? ` — Winner: ${state.winners.join(', ')}` : ''}
                  {state.hands && (
                    <span className="ml-2">Showdown: {Object.entries(state.hands).map(([n, v]: any) => `${n}: ${(v.hole_cards||[]).join(' ')}`).join(' | ')}</span>
                  )}
                </div>
                <button className="bg-blue-600 px-3 py-2 rounded" onClick={nextHand}>Next Hand</button>
              </div>
            )}

            {state.action_log && (
              <div className="bg-green-800 p-3 rounded">
                <div className="font-semibold mb-2">Log</div>
                <div className="max-h-48 overflow-auto space-y-1 text-sm">
                  {state.action_log.map((line: string, idx: number) => (
                    <div key={idx}>• {line}</div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}


