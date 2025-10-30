import React, { useEffect, useState } from 'react'

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
}

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [sessionId, setSessionId] = useState<string>('')
  const [state, setState] = useState<GameState | null>(null)
  const [raiseTo, setRaiseTo] = useState<number>(0)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string>('')

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
                  <div className="mt-2">Hole: {(p.hole_cards || (p.name === 'You' ? [] : [])).join(' ') || (p.name === 'You' ? '?? ??' : '?? ??')}</div>
                </div>
              ))}
            </div>

            <div className="bg-green-800 p-4 rounded space-x-2 flex items-center">
              <button className="bg-red-600 px-3 py-2 rounded" onClick={() => act('fold')}>Fold</button>
              <button className="bg-gray-600 px-3 py-2 rounded" onClick={() => act('check')}>Check</button>
              <button className="bg-yellow-600 px-3 py-2 rounded" onClick={() => act('call', state.current_bet)}>Call</button>
              <input type="number" className="text-black px-2 py-1 rounded" value={raiseTo} onChange={(e) => setRaiseTo(parseInt(e.target.value || '0'))} placeholder="Raise to" />
              <button className="bg-blue-600 px-3 py-2 rounded" onClick={() => act('raise', raiseTo)}>Raise</button>
              <button className="bg-purple-600 px-3 py-2 rounded ml-auto" onClick={botAct}>Bot Act</button>
              {error && <div className="text-red-300 text-sm ml-3">{error}</div>}
            </div>

            {state.is_complete && (
              <div className="bg-green-800 p-4 rounded flex items-center space-x-3">
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


