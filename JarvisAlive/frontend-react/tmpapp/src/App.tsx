import { useMemo, useState, useRef, useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Sidebar } from './components/Sidebar'
import { SendHorizonal, Globe, Mic, X } from 'lucide-react'
import { OfficeView } from './components/OfficeView'
import InboxPage from './pages/Inbox'
import OutcomesPage from './pages/Outcomes'
import SuggestionsPage from './pages/Suggestions'
import AgentChatPage from './pages/AgentChat'
import WorkflowForm from './components/WorkflowForm'

// API Configuration
const API_BASE = 'http://localhost:8000'

// API Helper Functions
const apiCall = async (endpoint: string, options: RequestInit = {}): Promise<any> => {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })
  
  if (!response.ok) {
    throw new Error(`API call failed: ${response.statusText}`)
  }
  
  return await response.json()
}

// Minimal typings for Web Speech API (cross-browser)
interface SimpleSpeechRecognitionEvent {
  resultIndex: number
  results: Array<{ 0: { transcript: string } }>
}
interface SimpleSpeechRecognition {
  lang: string
  interimResults: boolean
  onresult: (event: SimpleSpeechRecognitionEvent) => void
  onend: () => void
  onerror: (event: any) => void
  start: () => void
  stop: () => void
}


// Remove hardcoded coffee shop trigger and make it general-purpose
// const EXAMPLE_PROMPTS = [
//   "Create a sustainable fashion brand",
//   "Start a tech consulting company", 
//   "Launch a gourmet pen company",
//   "Build a local coffee shop",
//   "Develop a fitness app business"
// ]

function DemoRouteContent({ onOpenWebsiteDemo }: { onOpenWebsiteDemo: () => void }) {
  const [input, setInput] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [currentStep, setCurrentStep] = useState<'input' | 'research' | 'branding' | 'complete'>('input')
  const [isListening, setIsListening] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [websocket, setWebsocket] = useState<WebSocket | null>(null)
  const [marketResearch, setMarketResearch] = useState<any>(null)
  const [brandingOptions, setBrandingOptions] = useState<any>(null)
  const [selectedBranding, setSelectedBranding] = useState<any>(null)
  const [businessRequest, setBusinessRequest] = useState('')
  const [currentAgent, setCurrentAgent] = useState<string>('')
  const [currentTask, setCurrentTask] = useState<string>('')
  
  const recognitionRef = useRef<SimpleSpeechRecognition | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Website generation state
  const [websiteFlow, setWebsiteFlow] = useState<'idle' | 'loading' | 'ready'>('idle')
  const [websiteProgress, setWebsiteProgress] = useState(0)
  const [websiteStep, setWebsiteStep] = useState('')

  // Initialize session and WebSocket connection
  useEffect(() => {
    initializeSession()
    return () => {
      if (websocket) {
        websocket.close()
      }
    }
  }, [])

  const initializeSession = async () => {
    try {
      // Create session
      const sessionData = await apiCall('/api/sessions', {
        method: 'POST',
        body: JSON.stringify({
          user_id: 'demo_user',
          metadata: { demo_type: 'general_business_creation' }
        })
      })
      
      setSessionId(sessionData.session_id)
      
      // Load agents (available but not stored in state for now)
      await apiCall('/api/agents')
      
      // Setup WebSocket
      setupWebSocket(sessionData.session_id)
      
    } catch (error) {
      console.error('Failed to initialize session:', error)
    }
  }

  const setupWebSocket = (sessionId: string) => {
    const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`)
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      handleWebSocketMessage(message)
    }
    
    ws.onclose = () => {
      console.log('WebSocket closed, attempting to reconnect...')
      setTimeout(() => setupWebSocket(sessionId), 3000)
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    
    setWebsocket(ws)
  }

  const handleWebSocketMessage = (message: any) => {
    console.log('WebSocket message:', message)
    
    switch (message.type) {
      case 'business_creation_started':
        setIsProcessing(true)
        setCurrentStep('research')
        setBusinessRequest(message.data.request)
        break
        
      case 'agent_working':
        setCurrentAgent(message.data.agent)
        setCurrentTask(message.data.task)
        break
        
      case 'market_research_complete':
        setMarketResearch(message.data)
        setCurrentStep('branding')
        break
        
      case 'branding_complete':
        setBrandingOptions(message.data.branding)
        setCurrentStep('complete')
        setIsProcessing(false)
        break
        
      case 'website_generation_started':
        setWebsiteFlow('loading')
        setWebsiteProgress(0)
        break
        
      case 'website_progress':
        setWebsiteProgress(message.data.progress)
        setWebsiteStep(message.data.current_task)
        break
        
      case 'website_complete':
        setWebsiteFlow('ready')
        break
        
      default:
        console.log('Unhandled message type:', message.type)
    }
  }

  const handleSend = async () => {
    const text = input.trim()
    if (!text || !sessionId) return

    setInput('')
    setIsProcessing(true)
    
    try {
      // Send any business request directly to orchestrator
      await apiCall('/api/messages', {
        method: 'POST',
        body: JSON.stringify({
          session_id: sessionId,
          agent_id: 'orchestrator',
          message: text
        })
      })
      
    } catch (error) {
      console.error('Failed to send message:', error)
      setIsProcessing(false)
    }
  }

  const handleBrandingSelection = async (option: any) => {
    setSelectedBranding(option)
    
    try {
      await apiCall('/api/branding/select', {
        method: 'POST',
        body: JSON.stringify({
          session_id: sessionId,
          option: option
        })
      })
    } catch (error) {
      console.error('Failed to select branding:', error)
    }
  }

  const handleWebsiteGeneration = async () => {
    try {
      await apiCall('/api/website/generate', {
        method: 'POST',
        body: JSON.stringify({
          session_id: sessionId,
          business_details: {
            request: businessRequest,
            branding: selectedBranding,
            market_research: marketResearch
          }
        })
      })
    } catch (error) {
      console.error('Failed to generate website:', error)
    }
  }

  const toggleListening = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Speech recognition not supported in this browser')
      return
    }

    if (isListening) {
      recognitionRef.current?.stop()
      setIsListening(false)
      return
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    const recognition: SimpleSpeechRecognition = new SpeechRecognition()
    
    recognition.lang = 'en-US'
    recognition.interimResults = false
    
    recognition.onresult = (event: SimpleSpeechRecognitionEvent) => {
      const transcript = event.results[event.resultIndex][0].transcript
      setInput(transcript)
      setIsListening(false)
    }
    
    recognition.onend = () => {
      setIsListening(false)
    }
    
    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error)
      setIsListening(false)
    }
    
    recognitionRef.current = recognition
    recognition.start()
    setIsListening(true)
  }

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  return (
    <>
      {currentStep === 'input' && (
        <div className="p-8 max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <div className="inline-block p-4 rounded-full bg-gradient-to-br from-indigo-100 to-purple-100 mb-6">
              <div className="text-4xl">🚀</div>
            </div>
            <h1 className="text-4xl font-bold text-neutral-900 mb-4">
              Hey<span className="bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">Jarvis</span>
            </h1>
            <p className="text-xl text-neutral-600 mb-8">Your AI business orchestration platform</p>
            
            {!isProcessing && (
              <div className="max-w-2xl mx-auto">
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-2xl p-6 mb-6">
                  <div className="text-blue-800 font-semibold mb-3">💼 Tell Jarvis what business you want to create:</div>
                  <div className="text-sm text-blue-700">
                    Jarvis will coordinate with our market research and branding agents to build your complete business foundation.
                  </div>
                </div>
                
                <div className="rounded-2xl border border-neutral-200 bg-white flex items-center shadow-sm">
                  <input 
                    ref={inputRef}
                    className="w-full px-4 py-4 text-lg outline-none rounded-l-2xl" 
                    placeholder="Describe the business you want to create or launch..." 
                    value={input} 
                    onChange={(e) => setInput(e.target.value)} 
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()} 
                  />
                  <button 
                    className={`m-1 px-4 py-3 rounded-lg transition-colors ${
                      isListening ? 'bg-rose-600 text-white' : 'bg-neutral-200 hover:bg-neutral-300 text-neutral-800'
                    }`}
                    onClick={toggleListening} 
                    aria-label="Voice input" 
                    title="Voice input"
                  >
                    <Mic className="w-5 h-5" />
                  </button>
                  <button 
                    className="m-1 px-4 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors" 
                    onClick={handleSend} 
                    aria-label="Send" 
                    title="Send"
                    disabled={!input.trim()}
                  >
                    <SendHorizonal className="w-5 h-5" />
                  </button>
                </div>
              </div>
            )}
            
            {isProcessing && currentStep === ('research' as const) && (
              <div className="max-w-md mx-auto">
                <div className="bg-white rounded-2xl border border-neutral-200 shadow-lg p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-content animate-pulse">
                      <div className="text-white text-sm font-bold mx-auto">E</div>
                    </div>
                    <div>
                      <div className="text-lg font-semibold text-neutral-900">{currentAgent} is working...</div>
                      <div className="text-sm text-neutral-600">{currentTask}</div>
                    </div>
                  </div>
                  
                  <div className="text-sm text-neutral-700 bg-neutral-50 rounded-lg p-3">
                    <div className="font-medium mb-1">Your Request:</div>
                    <div>"{businessRequest}"</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {currentStep === 'branding' && marketResearch && (
        <div className="p-8">
          <div className="max-w-6xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-neutral-900 mb-2">Market Research Complete</h1>
              <p className="text-neutral-600">Edith analyzed the market for: "{businessRequest}"</p>
            </div>

            <div className="rounded-3xl border border-neutral-200 bg-white shadow-sm p-6 mb-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="text-2xl">📊</div>
                <div>
                  <div className="font-semibold text-neutral-900">Market Analysis Results</div>
                  <div className="text-sm text-neutral-600">Real analysis from our Market Research Agent</div>
                </div>
              </div>
              
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <div className="font-medium text-blue-900 mb-2">Market Size & Demographics</div>
                    <div className="text-sm text-blue-800">{marketResearch.research?.market_size}</div>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg">
                    <div className="font-medium text-green-900 mb-2">Competitive Landscape</div>
                    <div className="text-sm text-green-800">{marketResearch.research?.competition}</div>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="p-4 bg-purple-50 rounded-lg">
                    <div className="font-medium text-purple-900 mb-2">Market Trends</div>
                    <div className="text-sm text-purple-800">{marketResearch.research?.trends}</div>
                  </div>
                  <div className="p-4 bg-orange-50 rounded-lg">
                    <div className="font-medium text-orange-900 mb-2">Target Audience</div>
                    <div className="text-sm text-orange-800">{marketResearch.research?.target_audience}</div>
                  </div>
                </div>
              </div>
              
              <div className="mt-4 p-4 bg-neutral-50 rounded-lg">
                <div className="font-medium text-neutral-900 mb-1">Market Research Agent Recommendation:</div>
                <div className="text-sm text-neutral-700">{marketResearch.recommendations}</div>
              </div>
            </div>

            {currentAgent && (
              <div className="text-center">
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-800 rounded-lg">
                  <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                  <span className="font-medium">{currentAgent} is {currentTask.toLowerCase()}...</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
      
      {currentStep === 'complete' && brandingOptions && (
        <div className="p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-neutral-900 mb-2">Business Foundation Complete</h1>
              <p className="text-neutral-600">Alfred created brand concepts for: "{businessRequest}"</p>
            </div>

            {/* Brand Concepts from Real Branding Agent */}
            <div className="rounded-3xl border border-neutral-200 bg-white shadow-sm p-6 mb-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="text-2xl">🎨</div>
                <div>
                  <div className="font-semibold text-neutral-900">Brand Identity Concepts</div>
                  <div className="text-sm text-neutral-600">Real output from our Branding Agent</div>
                </div>
              </div>
              
              <div className="grid md:grid-cols-3 gap-4 mb-6">
                {brandingOptions.brand_concepts?.map((concept: any, idx: number) => (
                  <div 
                    key={idx} 
                    className={`border-2 rounded-xl p-4 cursor-pointer transition-all ${
                      selectedBranding?.name === concept.name ? 'border-indigo-500 bg-indigo-50' : 'border-neutral-200 hover:border-neutral-300'
                    }`}
                    onClick={() => handleBrandingSelection(concept)}
                  >
                    <div className="font-medium text-neutral-900 mb-2">{concept.name}</div>
                    <div className="text-sm text-neutral-600">{concept.style}</div>
                  </div>
                ))}
              </div>

              {/* Color Palettes from Real Branding Agent */}
              <div className="mb-6">
                <div className="font-medium text-neutral-900 mb-3">Color Palettes</div>
                <div className="grid grid-cols-3 gap-4">
                  {brandingOptions.color_palettes?.map((palette: any, idx: number) => (
                    <div key={idx} className="flex gap-2">
                      <div className="w-8 h-8 rounded-full" style={{backgroundColor: palette.primary}}></div>
                      <div className="w-8 h-8 rounded-full" style={{backgroundColor: palette.secondary}}></div>
                      <div className="w-8 h-8 rounded-full" style={{backgroundColor: palette.accent}}></div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Domain Suggestions (Mock as requested) */}
              <div className="mb-6">
                <div className="font-medium text-neutral-900 mb-3">Domain Suggestions (via GoDaddy)</div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {['business.com', 'venture.co', 'startup.io', 'company.net'].map((domain, idx) => (
                    <div key={idx} className="p-3 bg-neutral-50 rounded-lg text-center">
                      <div className="text-sm font-medium">{domain}</div>
                      <div className="text-xs text-green-600">Available</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex gap-3">
                <button 
                  className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2"
                  onClick={handleWebsiteGeneration}
                  disabled={!selectedBranding}
                >
                  <Globe className="w-4 h-4" />
                  Generate Website
                </button>
                <button className="px-6 py-2 border border-neutral-200 rounded-lg hover:bg-neutral-50 transition-colors">
                  Request Branding Revisions
                </button>
                <button className="px-6 py-2 border border-neutral-200 rounded-lg hover:bg-neutral-50 transition-colors">
                  Get More Market Research
                </button>
              </div>
            </div>

            {/* Website Generation Progress - Connected to Real Backend Function */}
            {websiteFlow === 'loading' && (
              <div className="rounded-3xl border border-neutral-200 bg-white shadow-sm p-6 mb-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center animate-pulse">
                    <div className="text-white text-sm font-bold">W</div>
                  </div>
                  <div>
                    <div className="font-semibold text-neutral-900">Website Generation In Progress...</div>
                    <div className="text-sm text-neutral-600">{websiteStep}</div>
                  </div>
                </div>
                <div className="w-full bg-neutral-200 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all duration-1000"
                    style={{ width: `${websiteProgress}%` }}
                  ></div>
                </div>
                <div className="mt-2 text-sm text-neutral-600">
                  Using real website generation function from backend...
                </div>
              </div>
            )}

            {/* Website Complete - Real Backend Function Result */}
            {websiteFlow === 'ready' && (
              <div className="rounded-3xl border border-neutral-200 bg-white shadow-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="text-2xl">🌐</div>
                    <div>
                      <div className="font-semibold text-neutral-900">Website Generated Successfully!</div>
                      <div className="text-sm text-neutral-600">Generated using our real website generation function</div>
                    </div>
                  </div>
                  <div className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">Complete</div>
                </div>

                <div className="flex gap-3">
                  <button 
                    className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                    onClick={onOpenWebsiteDemo}
                  >
                    View Generated Website
                  </button>
                  <button className="px-6 py-2 border border-neutral-200 rounded-lg hover:bg-neutral-50 transition-colors">
                    Download Website Files
                  </button>
                  <button className="px-6 py-2 border border-neutral-200 rounded-lg hover:bg-neutral-50 transition-colors">
                    Request Website Changes
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}

function App() {
  const [showOffice, setShowOffice] = useState(false)
  const agents = useMemo(() => ([
    { name: 'MJ', role: 'Marketing', avatar: '/MJ copy.png', dept: 'Marketing' as const },
    { name: 'Alfred', role: 'Sales', avatar: '/Alfred copy.png', dept: 'Sales' as const },
    { name: 'Edith', role: 'Engineering', avatar: '/Ed1th copy.png', dept: 'Engineering' as const },
    { name: 'Jarvis', role: 'Orchestration', avatar: '/Jarvis copy.png', dept: 'Orchestration' as const },
  ]), [])

  const coordination = useMemo(() => ([['Marketing', 'Engineering'] as [
    'Marketing' | 'Sales' | 'Engineering' | 'Orchestration',
    'Marketing' | 'Sales' | 'Engineering' | 'Orchestration',
  ]]), [])

  type ChatMessage = { from: 'edith' | 'user'; text: string }
  const [showWebsiteDemo, setShowWebsiteDemo] = useState(false)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [chatInput, setChatInput] = useState('')
  const [showWorkflowForm, setShowWorkflowForm] = useState(false)

  // Global context panel (persists across routes)
  const [panel, setPanel] = useState<{ open: boolean; tab: 'inbox' | 'outcomes' | 'suggestions' }>({ open: false, tab: 'inbox' })

  const openWebsiteDemo = () => {
    setShowWebsiteDemo(true)
    setChatMessages([
      { from: 'edith', text: 'Welcome to Copper & Crumb. This is a first draft landing page to showcase the brand, story, and a simple CTA.' },
      { from: 'edith', text: 'What would you like on the menu for launch? I can note drinks and pastries you have in mind.' },
    ])
    setChatInput('')
  }

  const closeWebsiteDemo = () => setShowWebsiteDemo(false)

  const sendChat = (text?: string) => {
    const value = (text ?? chatInput).trim()
    if (!value) return
    setChatMessages((msgs) => [...msgs, { from: 'user', text: value }])
    setChatInput('')
    setTimeout(() => {
      setChatMessages((msgs) => [
        ...msgs,
        { from: 'edith', text: `Great. I’ll add “${value}” to the draft menu and prep a price test.` },
      ])
    }, 500)
  }

  return (
    <BrowserRouter>
    <div className="h-full grid grid-cols-[280px_1fr]">
      <Sidebar />

      <main className="relative border-l border-neutral-200 bg-white/70 backdrop-blur">
        {/* Slim expandable tabs removed from global floating position; now rendered within page headers */}

        <Routes>
          <Route path="/inbox" element={<InboxPage />} />
          <Route path="/outcomes" element={<OutcomesPage />} />
          <Route path="/suggestions" element={<SuggestionsPage />} />
          <Route path="/chat/:agentId" element={<AgentChatPage />} />
          <Route path="*" element={<DemoRouteContent onOpenWebsiteDemo={openWebsiteDemo} />} />
        </Routes>

        {/* Right slide-over panel (global) */}
        {panel.open && (
          <div className="fixed inset-y-0 right-0 z-30 pointer-events-none">
            <div className="h-full w-[520px] max-w-[92vw] bg-white border-l border-neutral-200 shadow-xl pointer-events-auto">
              <div className="sticky top-0 bg-white border-b border-neutral-100 p-3 flex items-center justify-between">
                <div className="font-semibold capitalize">{panel.tab}</div>
                <button className="w-8 h-8 grid place-items-center rounded-full border" onClick={() => setPanel((p) => ({ ...p, open: false }))} aria-label="Close panel"><X className="w-4 h-4"/></button>
              </div>
              <div className="h-[calc(100%-48px)] overflow-y-auto">
                <div className="relative h-full">
                  {panel.tab === 'inbox' && <InboxPage />}
                  {panel.tab === 'outcomes' && <OutcomesPage />}
                  {panel.tab === 'suggestions' && <SuggestionsPage />}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Website demo overlay with iframe and chat */}
        {showWebsiteDemo && (
          <div className="fixed inset-0 z-30">
            <div className="absolute inset-0 bg-black/50" />
            <div className="absolute inset-4 rounded-3xl overflow-hidden shadow-2xl">
              <iframe src="/copper-crumb-preview-2.html" title="Website demo" className="w-full h-full border-0 bg-white" />
              {/* Close button */}
              <button
                className="absolute top-4 right-4 w-9 h-9 rounded-full grid place-items-center bg-white/90 border border-neutral-200 shadow hover:bg-white"
                onClick={closeWebsiteDemo}
                aria-label="Close website demo"
                title="Close"
              >
                <X className="w-4 h-4 text-neutral-700" />
              </button>
              {/* Chat overlay */}
              <div className="absolute bottom-4 right-4 w-[360px] max-w-[92vw] rounded-2xl border border-neutral-200 bg-white/95 backdrop-blur p-3 shadow-lg">
                <div className="text-sm font-medium text-neutral-800 mb-2">Chat with Edith</div>
                <div className="max-h-[46vh] overflow-y-auto space-y-2 pr-1">
                  {chatMessages.map((m, i) => (
                    <div key={i} className={`flex ${m.from === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`${m.from === 'user' ? 'bg-indigo-600 text-white' : 'bg-neutral-100 text-neutral-800'} px-3 py-2 rounded-2xl max-w-[80%] whitespace-pre-wrap`}>{m.text}</div>
                    </div>
                  ))}
                </div>
                {/* Suggestion chips */}
                <div className="flex flex-wrap gap-2 my-2">
                  {['Espresso', 'Cappuccino', 'Seasonal latte', 'Croissant', 'Cinnamon roll'].map((s) => (
                    <button key={s} className="text-xs px-2 py-1 rounded-full border border-neutral-200 hover:bg-neutral-50" onClick={() => sendChat(s)}>{s}</button>
                  ))}
                </div>
                <div className="flex items-center gap-2">
                  <input
                    className="flex-1 px-3 py-2 rounded-lg border border-neutral-300 outline-none"
                    placeholder="e.g., Espresso, cold brew, chocolate croissant"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && sendChat()}
                  />
                  <button className="px-3 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700" onClick={() => sendChat()} aria-label="Send message" title="Send message">
                    <SendHorizonal className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        <WorkflowForm isOpen={showWorkflowForm} onClose={()=>setShowWorkflowForm(false)} />
        <OfficeView isOpen={showOffice} onClose={() => setShowOffice(false)} agents={agents} coordination={coordination} />
      </main>
    </div>
    </BrowserRouter>
  )
}

export default App
