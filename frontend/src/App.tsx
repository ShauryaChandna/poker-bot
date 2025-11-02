import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
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
  big_blind?: number
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
  const [isPaused, setIsPaused] = useState<boolean>(false)
  const [displayMode, setDisplayMode] = useState<'dollars' | 'bb'>('dollars')
  const [gameHistory, setGameHistory] = useState<Array<{handNumber: number, actions: string[], holeCards: Record<string, string[]>, communityCards: string[]}>>([])
  const [showGameOverPopup, setShowGameOverPopup] = useState<boolean>(false)
  const [showGameReview, setShowGameReview] = useState<boolean>(false)
  const playerTimerRef = useRef<any>(null)
  const botTimerRef = useRef<any>(null)
  const nextHandTimerRef = useRef<any>(null)
  const lastCompleteHandRef = useRef<number | null>(null)
  const lastHandNumberRef = useRef<number | null>(null)
  const lastStreetRef = useRef<string | null>(null)
  const playerTimerStartRef = useRef<number | null>(null)

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
      if (!res.ok) {
        console.error('Bot action failed:', res.status, res.statusText)
        return
      }
      const data = await res.json()
      setState(data)
    } catch (e) {
      console.error('Bot action error:', e)
    }
  }

  const nextHandCallback = useCallback(async () => {
    if (!sessionId) return
    try {
      console.log('Auto-starting next hand...')
      const res = await fetch(`${API}/next_hand`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId }) })
      if (!res.ok) throw new Error('Next hand failed')
      const data = await res.json()
      setState(data)
      lastCompleteHandRef.current = null // Reset tracking after starting new hand
    } catch (e) {
      console.error('Failed to start next hand:', e)
      // keep UI stable
    }
  }, [sessionId])

  useEffect(() => {
    if (isPaused || !sessionId) return
    const id = setInterval(() => {
      refresh()
    }, 1500)
    return () => clearInterval(id)
  }, [sessionId, isPaused])

  // Turn timers and auto-actions
  const stateRef = useRef(state)
  useEffect(() => {
    stateRef.current = state
  }, [state])

  // Reset player timer when new hand starts or street changes
  useEffect(() => {
    if (!state) return
    const currentHandNumber = state.hand_number
    const lastHandNumber = lastHandNumberRef.current
    const currentStreet = state.street
    const lastStreet = lastStreetRef.current
    
    // If hand number changed and it's not complete, this is a new hand - reset timer
    if (lastHandNumber !== null && currentHandNumber !== lastHandNumber && !state.is_complete) {
      setPlayerTimeLeft(20000) // Reset to full time
      playerTimerStartRef.current = null
      if (playerTimerRef.current) {
        clearInterval(playerTimerRef.current)
        playerTimerRef.current = null
      }
    }
    
    // If street changed (preflop -> flop -> turn -> river), reset timer
    if (lastStreet !== null && currentStreet !== null && currentStreet !== lastStreet && !state.is_complete) {
      setPlayerTimeLeft(20000) // Reset to full time
      playerTimerStartRef.current = null
      if (playerTimerRef.current) {
        clearInterval(playerTimerRef.current)
        playerTimerRef.current = null
      }
    }
    
    lastHandNumberRef.current = currentHandNumber
    lastStreetRef.current = currentStreet
  }, [state?.hand_number, state?.street, state?.is_complete])

  useEffect(() => {
    // Stop all timers if paused
    if (isPaused) {
      if (playerTimerRef.current) {
        clearInterval(playerTimerRef.current)
        playerTimerRef.current = null
      }
      if (botTimerRef.current) {
        clearInterval(botTimerRef.current)
        botTimerRef.current = null
      }
      return
    }
    
    // Stop player timer if hand is complete (showdown) - preserve remaining time
    if (state?.is_complete) {
      if (playerTimerRef.current) {
        clearInterval(playerTimerRef.current)
        playerTimerRef.current = null
      }
      // Don't reset playerTimeLeft or playerTimerStartRef - keep the current value
      // But still handle bot timer
      if (botTimerRef.current) {
        clearInterval(botTimerRef.current)
        botTimerRef.current = null
      }
      return
    }
    
    if (playerTimerRef.current) { clearInterval(playerTimerRef.current); playerTimerRef.current = null }
    if (botTimerRef.current) { clearInterval(botTimerRef.current); botTimerRef.current = null }
    
    if (!state?.awaiting_player) return
    const humanName = 'You'
    if (state.awaiting_player === humanName) {
      const total = 20000
      
      // If we have a saved start time from earlier in this hand, continue from there
      // Otherwise, start fresh
      if (playerTimerStartRef.current === null) {
        const startAt = Date.now()
        playerTimerStartRef.current = startAt
        setPlayerTimeLeft(total)
      }
      
      playerTimerRef.current = setInterval(() => {
        const startAt = playerTimerStartRef.current
        if (!startAt) return
        const left = Math.max(0, total - (Date.now() - startAt))
        setPlayerTimeLeft(left)
        if (left <= 0) {
          clearInterval(playerTimerRef.current)
          playerTimerRef.current = null
          playerTimerStartRef.current = null
          // Auto-action: use latest state from ref
          const currentState = stateRef.current
          if (currentState?.legal_actions?.check) {
            act('check')
          } else if (currentState?.legal_actions?.fold) {
            act('fold')
          } else if (currentState?.legal_actions?.call) {
            act('call', currentState.current_bet)
          }
        }
      }, 100)
    } else {
      const total = 3000
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
  }, [state?.awaiting_player, state?.is_complete, isPaused])

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
    
    // Determine color based on suit
    let textColor = 'text-black' // default for spades
    if (value) {
      if (value.includes('♥')) {
        textColor = 'text-red-600' // hearts
      } else if (value.includes('♦')) {
        textColor = 'text-blue-600' // diamonds
      } else if (value.includes('♣')) {
        textColor = 'text-green-600' // clubs
      } else if (value.includes('♠')) {
        textColor = 'text-black' // spades
      }
    }
    
    return (
      <motion.div
        initial={shouldAnimate ? { opacity: 0, y: -10 } : false}
        animate={{ opacity: 1, y: 0 }}
        transition={shouldAnimate ? { delay: (idx || 0) * 0.05 } : undefined}
        className={`w-12 h-16 rounded-md border border-black shadow-sm flex items-center justify-center select-none ${faceDown ? 'bg-red-700' : 'bg-white'}`}
        style={faceDown ? pattern : undefined}
      >
        {!faceDown && <span className={`font-semibold ${textColor}`}>{value}</span>}
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
  
  // Helper function to format amounts based on display mode
  const formatAmount = (amount: number): string => {
    if (displayMode === 'bb' && state?.big_blind) {
      const bbAmount = amount / state.big_blind
      return bbAmount.toFixed(2)
    }
    return amount.toString()
  }
  
  // Helper to get suffix for display mode
  const getAmountSuffix = (): string => {
    return displayMode === 'bb' ? ' BB' : ''
  }

  // Track game history and detect game over
  useEffect(() => {
    if (!state) return
    
    // Check if hand just completed - add to history
    const handJustCompleted = state.is_complete && 
      (lastCompleteHandRef.current === null || lastCompleteHandRef.current !== state.hand_number)
    
    if (handJustCompleted) {
      console.log(`Hand ${state.hand_number} completed, marking as processed`)
      // Mark this hand as processed FIRST to prevent re-processing
      lastCompleteHandRef.current = state.hand_number
      
      // Add to game history
      const holeCards: Record<string, string[]> = {}
      if (state.hands) {
        Object.entries(state.hands).forEach(([name, hand]) => {
          holeCards[name] = hand.hole_cards || []
        })
      }
      setGameHistory(prev => [...prev, {
        handNumber: state.hand_number,
        actions: state.action_log || [],
        holeCards,
        communityCards: state.community_cards || []
      }])
      
      // Check if game is over (any player stack <= 0)
      const gameOver = state.players.some(p => p.stack <= 0)
      if (gameOver) {
        console.log('Game over detected')
        setShowGameOverPopup(true)
        // Don't start next hand if game is over
        return
      }
      
      // Auto-start next hand after 5 seconds when hand completes (if not paused)
      // Clear any existing timer first
      if (nextHandTimerRef.current) {
        clearTimeout(nextHandTimerRef.current)
        nextHandTimerRef.current = null
      }
      
      if (!isPaused) {
        // Start timer to move to next hand - capture sessionId in closure
        const currentSessionId = sessionId
        console.log(`Starting 5-second timer for next hand (session: ${currentSessionId})`)
        nextHandTimerRef.current = setTimeout(() => {
          console.log('Timer fired, calling nextHandCallback...')
          if (currentSessionId) {
            nextHandCallback()
          } else {
            console.log('No session ID, skipping nextHandCallback')
          }
        }, 5000)
      } else {
        console.log('Game is paused, not starting timer')
      }
    }
    
    // Clear next hand timer if paused (separate check for when pause state changes)
    if (isPaused && nextHandTimerRef.current) {
      console.log('Game paused, clearing timer')
      clearTimeout(nextHandTimerRef.current)
      nextHandTimerRef.current = null
    }
    
    // Don't reset tracking here - let nextHandCallback reset it when starting a new hand
    // This prevents the tracking from being cleared prematurely
    
    // Only cleanup timer on unmount or when dependencies change in a way that invalidates the timer
    return () => {
      // Don't clear timer on every render - only on unmount
      // The timer should persist across state updates
    }
  }, [state?.is_complete, state?.hand_number, sessionId, nextHandCallback, isPaused, state?.players])

  // Determine winner name
  const winnerName = useMemo(() => {
    if (!state?.winners || state.winners.length === 0) return null
    return state.winners[0]
  }, [state?.winners])

  // Track which action log entries we've already shown
  const lastShownBotActionIndex = useRef<number>(-1)
  const lastShownHumanActionIndex = useRef<number>(-1)
  const lastHandNumber = useRef<number>(-1)
  const [shownBotAction, setShownBotAction] = useState<string | null>(null)
  const [shownHumanAction, setShownHumanAction] = useState<string | null>(null)

  // Reset action tracking when hand number changes (new hand starts)
  useEffect(() => {
    if (state?.hand_number !== undefined && state.hand_number !== lastHandNumber.current) {
      lastHandNumber.current = state.hand_number
      lastShownBotActionIndex.current = -1
      lastShownHumanActionIndex.current = -1
      setShownBotAction(null)
      setShownHumanAction(null)
    }
  }, [state?.hand_number])

  // Check for new bot actions
  useEffect(() => {
    if (!state?.action_log || !bot || state.action_log.length === 0) return
    
    // Find the latest bot action we haven't shown yet
    for (let i = state.action_log.length - 1; i > lastShownBotActionIndex.current; i--) {
      const line = state.action_log[i].toLowerCase()
      const botNameLower = bot.name.toLowerCase()
      if (line.includes(botNameLower)) {
        let action: string | null = null
        // Check in order: folds, calls (using word boundary to avoid matching "checks"), raises/bets, then checks
        // Use word boundaries by checking for exact matches or patterns that won't match substrings incorrectly
        if (line.includes(' folds')) action = 'Fold'
        else if (line.includes(' calls ') || line.match(/calls \d/)) action = 'Call'
        else if (line.includes(' raises') || line.includes(' bets')) action = 'Raise'
        else if (line.includes(' checks')) action = 'Check'
        
        if (action) {
          lastShownBotActionIndex.current = i
          setShownBotAction(action)
          // Clear after 1 second
          setTimeout(() => setShownBotAction(null), 1000)
          break
        }
      }
    }
  }, [state?.action_log, bot])

  // Check for new human actions
  useEffect(() => {
    if (!state?.action_log || !human || state.action_log.length === 0) return
    
    // Find the latest human action we haven't shown yet
    for (let i = state.action_log.length - 1; i > lastShownHumanActionIndex.current; i--) {
      const line = state.action_log[i]
      if (line.includes(human.name)) {
        let action: string | null = null
        // Check in order: folds, calls (before checks), raises/bets, then checks
        if (line.includes('folds')) action = 'Fold'
        else if (line.includes('calls')) action = 'Call'
        else if (line.includes('raises') || line.includes('bets')) action = 'Raise'
        else if (line.includes('checks')) action = 'Check'
        
        if (action) {
          lastShownHumanActionIndex.current = i
          setShownHumanAction(action)
          // Clear after 1 second
          setTimeout(() => setShownHumanAction(null), 1000)
          break
        }
      }
    }
  }, [state?.action_log, human])

  return (
    <div className="min-h-screen bg-green-900 text-white p-4 relative">
      {/* Pause/Play button and BB/$ toggle - top left */}
      <div className="absolute top-4 left-4 flex items-center gap-2 z-50">
        <button
          onClick={() => setIsPaused(!isPaused)}
          className="w-10 h-10 flex items-center justify-center bg-black/30 hover:bg-black/50 rounded-lg transition-colors"
          aria-label={isPaused ? 'Resume' : 'Pause'}
        >
          {isPaused ? (
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
            </svg>
          ) : (
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          )}
        </button>
        <button
          onClick={() => setDisplayMode(displayMode === 'dollars' ? 'bb' : 'dollars')}
          className="w-10 h-10 flex items-center justify-center bg-black/30 hover:bg-black/50 rounded-lg transition-colors text-sm font-semibold"
          aria-label={displayMode === 'dollars' ? 'Switch to Big Blinds' : 'Switch to Dollars'}
        >
          {displayMode === 'dollars' ? 'BB' : '$'}
        </button>
      </div>
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

              {/* Community cards in center (shifted up slightly) */}
              <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 -mt-8 flex space-x-2">
                {community.map((c, i) => {
                  const prev = prevCommunityRef.current[i]
                  const shouldAnimate = !!c && !prev
                  return (
                    <Card key={i} value={c || ''} faceDown={!c} idx={i} shouldAnimate={shouldAnimate} />
                  )
                })}
              </div>

              {/* Pot text below community cards */}
              <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 mt-6 text-center">
                <div className="text-sm opacity-90">Pot</div>
                <div className="text-2xl font-bold">{formatAmount(state.pot)}{getAmountSuffix()}</div>
            </div>

              {/* Top player (Computer) */}
              {bot && (
                <div className="absolute left-1/2 -translate-x-1/2 top-6 flex flex-col items-center">
                  <div className="mb-2 text-sm bg-black/30 px-2 py-1 rounded">Bet: {formatAmount(bot.current_bet)}{getAmountSuffix()}</div>
                  <div className="relative flex items-center justify-center w-full">
                    {/* Dealer button positioned absolutely on the left */}
                    {state.dealer_name === bot.name && (
                      <div className="absolute left-0 w-6 h-6 rounded-full bg-yellow-300 text-black flex items-center justify-center text-xs font-bold" style={{ transform: 'translateX(-120%)' }}>D</div>
                    )}
                    {/* Cards container - always centered with fixed width */}
                    <div className="relative flex items-center justify-center space-x-2" style={{ width: '104px' }}>
                      <AnimatePresence>
                        {Array.from({ length: 2 }).map((_, i) => (
                          <Card key={i} idx={i} value={state.is_complete && state.hands && state.hands[bot.name] ? state.hands[bot.name].hole_cards[i] : ''} faceDown={!(state.is_complete && state.hands && state.hands[bot.name])} />
                        ))}
                      </AnimatePresence>
                    </div>
                    {/* Action pop-up for bot - positioned relative to outer container, centered between cards */}
                    {shownBotAction && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0, y: -20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0, y: -20 }}
                        transition={{ duration: 0.5, ease: "easeOut" }}
                        className="absolute top-0 left-1/2 -translate-x-1/2 -mt-20 bg-purple-400 text-white font-bold text-lg px-3 py-1 rounded-lg shadow-lg z-10 whitespace-nowrap"
                      >
                        {shownBotAction}
                      </motion.div>
                    )}
                    {/* Win! graphic for bot - positioned relative to outer container, centered between cards */}
                    {state.is_complete && winnerName === bot.name && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0, y: -20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                        className="absolute top-0 left-1/2 -translate-x-1/2 -mt-20 bg-yellow-400 text-black font-bold text-xl px-4 py-2 rounded-lg shadow-lg whitespace-nowrap"
                      >
                        Win!
                      </motion.div>
                    )}
                  </div>
                  {/* Bot timer bar (3s) */}
                  <div className="mt-2 w-40 h-2 bg-black/30 rounded overflow-hidden">
                    <div className="h-full bg-purple-400" style={{ width: `${Math.max(0, Math.min(100, 100 - (botTimeLeft/30)))}%` }} />
                  </div>
                  <div className="mt-2 text-sm">Stack: {formatAmount(bot.stack)}{getAmountSuffix()}</div>
                </div>
              )}

              {/* Bottom player (You) */}
              {human && (
                <div className="absolute left-1/2 -translate-x-1/2 bottom-6 flex flex-col items-center">
                  <div className="mb-2 text-sm bg-black/30 px-2 py-1 rounded">Bet: {formatAmount(human.current_bet)}{getAmountSuffix()}</div>
                  <div className="relative flex items-center justify-center w-full">
                    {/* Dealer button positioned absolutely on the left */}
                    {state.dealer_name === human.name && (
                      <div className="absolute left-0 w-6 h-6 rounded-full bg-yellow-300 text-black flex items-center justify-center text-xs font-bold" style={{ transform: 'translateX(-120%)' }}>D</div>
                    )}
                    {/* Cards container - always centered with fixed width */}
                    <div className="relative flex items-center justify-center space-x-2" style={{ width: '104px' }}>
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
                  </div>
                  {/* Player timer bar (20s) */}
                  <div className="mt-2 w-40 h-2 bg-black/30 rounded overflow-hidden">
                    <div className="h-full bg-blue-400" style={{ width: `${Math.max(0, Math.min(100, (playerTimeLeft/200)))}%` }} />
                  </div>
                  <div className="mt-2 text-sm relative">Stack: {formatAmount(human.stack)}{getAmountSuffix()}
                    {/* Action pop-up for human - positioned relative to stack text, aligned with left card */}
                    {shownHumanAction && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0, y: 20 }}
                        transition={{ duration: 0.5, ease: "easeOut" }}
                        className="absolute top-full mt-2 bg-blue-400 text-white font-bold text-lg px-3 py-1 rounded-lg shadow-lg z-10 whitespace-nowrap"
                        style={{ left: '50%', transform: 'translateX(calc(-50% - 60px))' }}
                      >
                        {shownHumanAction}
                      </motion.div>
                    )}
                    {/* Win! graphic for human - positioned relative to stack text, aligned with left card */}
                    {state.is_complete && winnerName === human.name && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                        className="absolute top-full mt-2 bg-yellow-400 text-black font-bold text-xl px-4 py-2 rounded-lg shadow-lg whitespace-nowrap"
                        style={{ left: '50%', transform: 'translateX(calc(-50% - 60px))' }}
                      >
                        Win!
                      </motion.div>
                    )}
                  </div>
                </div>
              )}
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
                    <div className="bg-white text-black px-3 py-1 rounded">{formatAmount(raiseTo || 0)}{getAmountSuffix()}</div>
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
          </div>
                  )}
                </div>

      {/* Game Over Popup */}
      {showGameOverPopup && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-green-900 rounded-lg p-8 shadow-2xl max-w-md w-full mx-4"
          >
            <h2 className="text-3xl font-bold text-center mb-6">
              {state && state.players.find(p => p.name === 'You')?.stack > 0 ? 'You Won!' : 'You Lost!'}
            </h2>
            <div className="flex flex-col space-y-3">
              <button
                onClick={() => {
                  setShowGameOverPopup(false)
                  setGameHistory([])
                  setSessionId('')
                  setState(null)
                }}
                className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold transition-colors"
              >
                Play Again
              </button>
              <button
                onClick={() => {
                  setShowGameOverPopup(false)
                  setShowGameReview(true)
                }}
                className="bg-yellow-600 hover:bg-yellow-700 px-6 py-3 rounded-lg font-semibold transition-colors"
              >
                Game Review
              </button>
              <button
                onClick={() => {
                  setShowGameOverPopup(false)
                  setGameHistory([])
                  setSessionId('')
                  setState(null)
                }}
                className="bg-gray-600 hover:bg-gray-700 px-6 py-3 rounded-lg font-semibold transition-colors"
              >
                Exit
              </button>
            </div>
          </motion.div>
              </div>
            )}

      {/* Game Review Modal */}
      {showGameReview && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-green-900 rounded-lg p-6 shadow-2xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col"
          >
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold">Game Review</h2>
              <button
                onClick={() => setShowGameReview(false)}
                className="text-white hover:text-gray-300 text-2xl"
              >
                ×
              </button>
            </div>
            <div className="overflow-y-auto flex-1">
              <table className="w-full text-left border-collapse">
                <thead className="bg-green-800 sticky top-0">
                  <tr>
                    <th className="p-3 border border-green-700">#</th>
                    <th className="p-3 border border-green-700">Your Cards</th>
                    <th className="p-3 border border-green-700">Bot Cards</th>
                    <th className="p-3 border border-green-700">Community Cards</th>
                    <th className="p-3 border border-green-700">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {gameHistory.map((hand, idx) => (
                    <tr key={idx} className="hover:bg-green-800/50">
                      <td className="p-3 border border-green-700 font-semibold">{hand.handNumber}</td>
                      <td className="p-3 border border-green-700">
                        {hand.holeCards['You']?.join(' ') || '—'}
                      </td>
                      <td className="p-3 border border-green-700">
                        {hand.holeCards['Computer']?.join(' ') || hand.holeCards[Object.keys(hand.holeCards).find(k => k !== 'You') || '']?.join(' ') || '—'}
                      </td>
                      <td className="p-3 border border-green-700">
                        {hand.communityCards.length > 0 ? hand.communityCards.join(' ') : '—'}
                      </td>
                      <td className="p-3 border border-green-700 text-sm">
                        <div className="space-y-1">
                          {hand.actions.map((action, i) => (
                            <div key={i}>{action}</div>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
                </div>
            <div className="mt-4 flex justify-end">
              <button
                onClick={() => {
                  setShowGameReview(false)
                  setGameHistory([])
                  setSessionId('')
                  setState(null)
                }}
                className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-lg font-semibold transition-colors"
              >
                Back to Home
              </button>
              </div>
          </motion.div>
          </div>
        )}
    </div>
  )
}


