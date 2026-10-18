import React from 'react'
import { createRoot } from 'react-dom/client'

function App(){
  return (
    <div style={{padding:24,fontFamily:'Inter, Arial'}}>
      <h1>LedgerLocket — CoinPilot Demo</h1>
      <p>Frontend placeholder. Use API at <code>http://localhost:5000</code></p>
      <p>This demo shows non-withdrawable credit balances and a button to mint credits (admin demo).</p>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)
