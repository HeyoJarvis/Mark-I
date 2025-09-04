import { useMemo, useState, useRef, useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Sidebar } from './components/Sidebar'
import { SendHorizonal, Palette, Activity, Globe, Mic, Check, X, ArrowRight, Plus, SlidersHorizontal, Search as SearchIcon, ChevronDown } from 'lucide-react'
import { OfficeView } from './components/OfficeView'
import InboxPage from './pages/Inbox'
import OutcomesPage from './pages/Outcomes'
import SuggestionsPage from './pages/Suggestions'
import AgentChatPage from './pages/AgentChat'
import WorkflowForm from './components/WorkflowForm'
import { apiService, type Agent } from './services/apiService'

// Minimal typings for Web Speech API (cross-browser)
interface SimpleSpeechRecognitionEvent {
  resultIndex: number
  results: Array<{ 0: { transcript: string } }>
}
interface SimpleSpeechRecognition {
  lang: string
  interimResults: boolean
  continuous: boolean
  onresult: ((event: SimpleSpeechRecognitionEvent) => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
}
interface WindowWithSpeech extends Window {
  SpeechRecognition?: { new (): SimpleSpeechRecognition }
  webkitSpeechRecognition?: { new (): SimpleSpeechRecognition }
}

function MarketDataDisplay({ marketData }: { marketData: any }) {
  if (!marketData) {
    return (
      <div className="text-sm text-neutral-500 italic">
        Loading market analysis...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Key Findings */}
      {marketData.key_findings && marketData.key_findings.length > 0 && (
        <div>
          <div className="text-xs text-neutral-500 mb-2">Key Findings</div>
          <ul className="space-y-1">
            {marketData.key_findings.slice(0, 3).map((finding: string, i: number) => (
              <li key={i} className="text-sm text-neutral-700 flex items-start gap-2">
                <span className="text-indigo-600 mt-0.5">•</span>
                <span>{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Market Size & Growth */}
      <div className="grid grid-cols-2 gap-4">
        {marketData.market_size && (
          <div>
            <div className="text-xs text-neutral-500">Market Size</div>
            <div className="text-sm font-medium text-neutral-800">{marketData.market_size}</div>
          </div>
        )}
        {marketData.growth_rate && (
          <div>
            <div className="text-xs text-neutral-500">Growth Rate</div>
            <div className="text-sm font-medium text-neutral-800">{marketData.growth_rate}</div>
          </div>
        )}
      </div>

      {/* Opportunities & Threats */}
      <div className="grid grid-cols-2 gap-4">
        {marketData.opportunities && marketData.opportunities.length > 0 && (
          <div>
            <div className="text-xs text-neutral-500 mb-1">Top Opportunities</div>
            {marketData.opportunities.slice(0, 2).map((opp: string, i: number) => (
              <div key={i} className="text-xs text-emerald-700">• {opp}</div>
            ))}
          </div>
        )}
        {marketData.threats && marketData.threats.length > 0 && (
          <div>
            <div className="text-xs text-neutral-500 mb-1">Key Threats</div>
            {marketData.threats.slice(0, 2).map((threat: string, i: number) => (
              <div key={i} className="text-xs text-rose-700">• {threat}</div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Small logo preview with fallback when image is missing
function LogoPreview({ src, alt }: { src: string; alt: string }) {
  const [ok, setOk] = useState(true)
  return (
    <div className="w-24 h-24 rounded-2xl ring-1 ring-neutral-200 bg-white grid place-items-center overflow-hidden">
      {ok ? (
        <img src={src} alt={alt} className="w-full h-full object-contain" onError={() => setOk(false)} />
      ) : (
        <div className="text-xs text-neutral-500">Logo</div>
      )}
    </div>
  )
}

const EXACT_TRIGGER = 'HeyJarvis I want to create a Coffee Shop'

function DemoRouteContent({ onOpenWebsiteDemo, onOpenWorkflowForm }: { onOpenWebsiteDemo: () => void; onOpenWorkflowForm: () => void }) {
  const [input, setInput] = useState('')
  const [demoUnlocked, setDemoUnlocked] = useState(false)
  const [triggerMessage, setTriggerMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [loadingSteps, setLoadingSteps] = useState<string[]>([])
  const [isListening, setIsListening] = useState(false)
  const [domainChoice, setDomainChoice] = useState<Record<string, 'accept' | 'reject' | undefined>>({})
  const [isConnected, setIsConnected] = useState(false)
  const [availableAgents, setAvailableAgents] = useState<Agent[]>([])
  const [marketData, setMarketData] = useState<any>(null)
  const [logoData, setLogoData] = useState<any>(null)
  const [brandingData, setBrandingData] = useState<any>(null)
  const [isGeneratingLogo, setIsGeneratingLogo] = useState(false)
  const [selectedDomain, setSelectedDomain] = useState<string>('')
  
  const recognitionRef = useRef<SimpleSpeechRecognition | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const domains = ['firstpour.cafe', 'cornerbloom.coffee', 'sproutandsteam.cafe', 'graniteandgrind.com', 'Copper&Crumb.co']

  const logoReady = domainChoice['Copper&Crumb.co'] === 'accept'

  // Website flow (Edith)
  const WEBSITE_LOADING_STEPS = [
    'Finding the coffee from somewhere…',
    'Negotiating with CSS about margins…',
    'Asking MJ for color opinions…',
    'Taming a rogue flexbox…',
    'Assembling hero image…',
    'Wiring the menu to thin air…',
    'Running Lighthouse by candlelight…',
    'Double-checking DNS just vibes…',
  ]
  const [websiteFlow, setWebsiteFlow] = useState<'idle' | 'loading' | 'ready'>('idle')
  const [webLoadIndex, setWebLoadIndex] = useState(0)

  const [legalOpen, setLegalOpen] = useState(false)

  const startWebsiteFlow = () => {
    if (websiteFlow !== 'idle') return
    setWebsiteFlow('loading')
    setWebLoadIndex(0)
    let idx = 0
    const stepMs = 1800
    const totalMs = 15000
    const stepTimer = setInterval(() => {
      idx = Math.min(idx + 1, WEBSITE_LOADING_STEPS.length - 1)
      setWebLoadIndex(idx)
    }, stepMs)
    setTimeout(() => {
      clearInterval(stepTimer)
      setWebsiteFlow('ready')
    }, totalMs)
  }

  // Initialize connection and fetch agents
  useEffect(() => {
    const initializeSystem = async () => {
      try {
        console.log('Initializing system...');
        
        // Create session
        await apiService.createSession();
        console.log('Session created:', apiService.getSessionId());
        
        // Fetch available agents
        const agents = await apiService.getAgents();
        setAvailableAgents(agents);
        console.log('Agents loaded:', agents);
        
        setIsConnected(true);
        
        // Check for demo session state
        try {
          const ready = sessionStorage.getItem('jarvis-demo-ready') === '1'
          const started = sessionStorage.getItem('jarvis-demo') === '1'
          if (ready) {
            setDemoUnlocked(true)
            setIsLoading(false)
            setTriggerMessage(EXACT_TRIGGER)
          } else if (started) {
            setInput(EXACT_TRIGGER)
            setTimeout(() => handleSend(), 0)
          }
        } catch {
          /* no-op */
        }
        
      } catch (error) {
        console.error('Failed to initialize system:', error);
        setIsConnected(false);
      }
    };

    initializeSystem();
    inputRef.current?.focus();
  }, []);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || !isConnected) return;

    setTriggerMessage(text);
    setIsLoading(true);
    setLoadingSteps([]);
    setInput('');

    try {
      // Determine which agent to use based on the request
      let agentId = 'jarvis'; // Default to jarvis (orchestrator) for complex requests
      
      // Simple keyword-based routing (you can make this more sophisticated)
      if (text.toLowerCase().includes('brand') && !text.toLowerCase().includes('create') && !text.toLowerCase().includes('business')) {
        agentId = 'branding';
      } else if (text.toLowerCase().includes('market') && !text.toLowerCase().includes('create') && !text.toLowerCase().includes('business')) {
        agentId = 'market_research';
      }
      
      console.log(`Sending request to ${agentId}:`, text);
      
      // Add some loading steps to show progress
      setLoadingSteps(['Analyzing your request...']);
      
      const response = await apiService.sendMessage(agentId, text);
      
      if (response.success) {
        console.log('Response received:', response);
        
        // Parse the response to update UI components
        parseAgentResponse(response, response.agent_id);
        
        setIsLoading(false);
        setDemoUnlocked(true);
        
        // Save demo state
        try {
          sessionStorage.setItem('jarvis-demo', '1');
          sessionStorage.setItem('jarvis-demo-ready', '1');
          sessionStorage.setItem('domains-list', JSON.stringify(domains));
        } catch { /* no-op */ }
      } else {
        console.error('Agent response error:', response.error);
        setLoadingSteps([...loadingSteps, `Error: ${response.error}`]);
        setTimeout(() => {
          setIsLoading(false);
        }, 2000);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      setLoadingSteps([...loadingSteps, 'Failed to send message. Please try again.']);
      setTimeout(() => {
        setIsLoading(false);
      }, 2000);
    }
  };

  const parseAgentResponse = (response: any, agentId: string) => {
    console.log('Parsing response from', agentId, ':', response);
    
    // Check if we have structured data in the response
    if (response.data) {
      // Handle structured data from the API
      if (response.data.market_research) {
        const marketData = response.data.market_research;
        setMarketData({
          market_opportunity_score: marketData.market_opportunity_score || 75,
          key_findings: marketData.key_findings || [],
          recommended_strategy: marketData.recommended_strategy || 'Focus on differentiation',
          market_size: marketData.market_size,
          growth_rate: marketData.growth_rate,
          target_audience: marketData.target_audience,
          competitors: marketData.competitors || [],
          threats: marketData.threats || [],
          opportunities: marketData.opportunities || []
        });
      }
      
      if (response.data.branding) {
        const brandData = response.data.branding;
        setBrandingData({
          brand_name: brandData.brand_name || 'Your Brand',
          tagline: brandData.tagline || 'Your tagline here',
          logo_prompt: brandData.logo_prompt || '',
          colors: brandData.color_palette || [],
          domain_suggestions: brandData.domain_suggestions || domains,
          brand_values: brandData.brand_values || [],
          target_audience: brandData.target_audience || ''
        });
        
        // Also set logo data if we have a logo prompt
        if (brandData.logo_prompt) {
          setLogoData({
            logo_url: '/coppercrumb.png', // Default logo for now
            logo_prompt: brandData.logo_prompt
          });
        }
      }
      
      return; // Exit early since we handled structured data
    }
    
    // Fallback to parsing text response (for backward compatibility)
    const responseText = typeof response === 'string' ? response : response.response || '';
    
    // Extract data from agent responses to populate the UI
    if (agentId === 'branding' || responseText.includes('Brand Design Complete')) {
      // Parse branding data
      const brandName = responseText.match(/\*\*Brand Name:\*\* (.+)/)?.[1];
      const logoPrompt = responseText.match(/\*\*Logo Concept:\*\* (.+)/)?.[1];
      const colors = responseText.match(/\*\*Colors:\*\* (.+)/)?.[1];
      const domains = responseText.match(/\*\*Domains:\*\* (.+)/)?.[1];
      
      if (brandName) {
        setBrandingData({
          brand_name: brandName,
          logo_prompt: logoPrompt,
          colors: colors?.split(', ') || [],
          domain_suggestions: domains?.split(', ') || []
        });
      }
    }
    
    if (agentId === 'market_research' || responseText.includes('Market Research Complete')) {
      // Parse market research data
      const score = responseText.match(/\*\*Opportunity Score:\*\* (\d+)/)?.[1];
      const findings = responseText.match(/\*\*Key Findings:\*\*\n((?:• .+\n?)*)/)?.[1];
      const strategy = responseText.match(/\*\*Strategy:\*\* (.+)/)?.[1];
      
      if (score) {
        setMarketData({
          market_opportunity_score: parseInt(score),
          key_findings: findings?.split('\n').filter(f => f.startsWith('•')).map(f => f.substring(2)) || [],
          recommended_strategy: strategy
        });
      }
    }
    
    if (agentId === 'jarvis' || agentId === 'orchestrator' || responseText.includes('Intelligence Orchestrator')) {
      // For orchestrator/jarvis responses, try to extract multiple types of data
      if (responseText.includes('brand') || responseText.includes('Brand')) {
        // Mock some branding data for orchestrator responses
        setBrandingData({
          brand_name: 'Copper & Crumb',
          logo_prompt: 'Modern coffee shop with copper accents and warm colors',
          colors: ['#8B4513', '#D2691E', '#F4E4BC'],
          domain_suggestions: domains
        });
      }
      
      if (responseText.includes('market') || responseText.includes('Market')) {
        // Mock some market data
        setMarketData({
          market_opportunity_score: 78,
          key_findings: [
            'Growing demand for artisanal coffee experiences',
            'High foot traffic area with limited competition',
            'Target demographic shows strong purchasing power'
          ],
          recommended_strategy: 'Premium positioning with local community focus'
        });
      }
    }
  };

  const toggleListening = () => {
    const w = window as WindowWithSpeech
    const Ctor = (w.SpeechRecognition || w.webkitSpeechRecognition) as unknown
    if (!Ctor) {
      alert('Voice-to-text is not supported in this browser.')
      return
    }
    if (isListening) {
      recognitionRef.current?.stop()
      setIsListening(false)
      return
    }
    const recognition: SimpleSpeechRecognition = new (Ctor as { new (): SimpleSpeechRecognition })()
    recognition.lang = 'en-US'
    recognition.interimResults = true
    recognition.continuous = false
    recognition.onresult = (event: SimpleSpeechRecognitionEvent) => {
      let transcript = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript
      }
      setInput((prev) => (transcript || prev))
    }
    recognition.onend = () => setIsListening(false)
    recognition.start()
    recognitionRef.current = recognition
    setIsListening(true)
  }

  const generateLogo = async () => {
    if (!brandingData || !selectedDomain) return;
    
    setIsGeneratingLogo(true);
    try {
      const result = await apiService.generateLogo(
        brandingData.brand_name,
        brandingData.logo_prompt || `Create a logo for ${brandingData.brand_name}`,
        brandingData.colors || []
      );
      
      if (result.success && result.logo_url) {
        setLogoData({
          logo_url: result.logo_url,
          logo_prompt: brandingData.logo_prompt
        });
      } else {
        console.error('Logo generation failed:', result.error);
      }
    } catch (error) {
      console.error('Failed to generate logo:', error);
    } finally {
      setIsGeneratingLogo(false);
    }
  }

  return (
    <>
        {/* Header */}
        <header className="sticky top-0 z-10 border-b border-neutral-100 bg-white px-6 py-5">
          <div className="flex items-center gap-4">
          <img src="/Jarvis copy.png" alt="Jarvis" className="w-10 h-10 rounded-full object-cover" />
            <div className="flex-1">
              <div className="font-semibold tracking-tight">Jarvis</div>
              <div className="text-xs text-neutral-500">
                Orchestration • {isConnected ? <span className="text-emerald-600">Online</span> : <span className="text-rose-600">Offline</span>}
              </div>
            </div>
          </div>
        </header>

      {/* Legal slide-over */}
      {legalOpen && (
        <div className="fixed inset-y-0 right-0 z-30 pointer-events-none">
          <div className="h-full w-[640px] max-w-[96vw] bg-white border-l border-neutral-200 shadow-xl pointer-events-auto">
            <div className="sticky top-0 bg-white border-b border-neutral-100 p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <img src="/lincolnn.png" alt="Lincoln" className="w-8 h-8 rounded-full object-cover" />
                <div className="font-semibold">Lincoln • Legal setup checklist</div>
              </div>
              <button className="w-8 h-8 grid place-items-center rounded-full border" onClick={() => setLegalOpen(false)} aria-label="Close legal"><X className="w-4 h-4"/></button>
            </div>
            <div className="h-[calc(100%-56px)] overflow-y-auto p-4 space-y-6">
              {([
                { title: 'Completed Legal Entity Setup', items: [
                  'Choose entity type',
                  'Check name availability & reserve',
                  'Register with state & appoint registered agent',
                  'File Articles & get stamped copy',
                  'Obtain Federal EIN (SS-4)',
                  'Generate Operating Agreement / Bylaws',
                ]},
                { title: 'Licenses & Permits Secured', items: [
                  'Local business license',
                  'Resale certificate / seller\'s permit',
                  'Zoning / occupancy clearance for warehouse',
                  'Warehouse permit (if required)',
                  'Importer of Record / Customs bond (if importing)',
                ]},
                { title: 'Compliance Checklist & Documentation', items: [
                  'CPSIA applicability check (children\'s pens)',
                  'ASTM D4236 labeling (if art materials)',
                  'California Proposition 65 labeling plan',
                  'Product safety & choking hazard warnings',
                  'Collect SDS & lab test results from suppliers',
                  'Compile compliance documentation package',
                ]},
                { title: 'Insurance Policy Recommendations', items: [
                  'General & Product Liability quotes (1M/2M)',
                  'Property/warehouse coverage',
                  'Workers\' comp (as needed)',
                  'Cyber liability',
                ]},
                { title: 'Regulatory Filing Confirmations', items: [
                  'IRS CP 575 EIN confirmation letter uploaded',
                  'State registration receipt on file',
                  'Resale certificate / seller\'s permit on file',
                  'FDA importer facility registration (if needed)',
                  'Customs bond confirmation (if importing)',
                ]},
              ] as { title: string; items: string[] }[]).map((sec) => (
                <div key={sec.title} className="rounded-2xl border border-neutral-200">
                  <div className="px-4 py-3 flex items-center justify-between bg-neutral-50 border-b border-neutral-200 rounded-t-2xl">
                    <div className="text-sm font-medium">{sec.title}</div>
                    <span className="text-xs text-neutral-500">PENDING</span>
                  </div>
                  <ul className="divide-y">
                    {sec.items.map((it) => (
                      <li key={it} className="flex items-center justify-between px-4 py-2">
                        <label className="flex items-center gap-3 text-sm text-neutral-800">
                          <input type="checkbox" disabled className="w-4 h-4 rounded border-neutral-300" />
                          <span>{it}</span>
                        </label>
                        <span className="text-xs text-neutral-500">PENDING</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

        {/* Transitional loading */}
        {isLoading && (
          <div className="absolute inset-0 pt-[72px] pb-[128px] overflow-y-auto">
            <div className="max-w-3xl mx-auto p-8">
              <div className="rounded-3xl border border-neutral-200 bg-white shadow-sm p-8">
                <div className="flex items-center gap-3 mb-4">
                  <div className="px-3 py-1.5 rounded-full bg-neutral-100 border border-neutral-200 text-neutral-700">{triggerMessage}</div>
                  <span className="text-xs text-neutral-500">starting workspace…</span>
                </div>

                <div className="space-y-4">
                  {loadingSteps.map((step, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <div className={`w-36 h-2 rounded bg-neutral-100 overflow-hidden`}>
                        <div className={`h-full bg-indigo-600 progress-bar scale-x-100`}></div>
                      </div>
                      <div className={`text-sm text-neutral-800`}>{step}</div>
                    </div>
                  ))}
                </div>

                <div className="mt-6 text-xs text-neutral-500">Jarvis is organizing work across the team…</div>
              </div>
            </div>
          </div>
        )}

        {/* Screen 1: make Jarvis initial screen match other chat UI */}
        {!demoUnlocked && !isLoading && (
                 <div className="absolute inset-0 flex flex-col">
          {/* Chat-like header */}
          <header className="shrink-0 px-6 py-5 bg-white">
            <div className="flex items-center gap-4">
              <img src="/Jarvis copy.png" alt="Jarvis" className="w-12 h-12 rounded-full object-cover" />
              <div>
                <div className="font-semibold text-base leading-tight">Jarvis</div>
                <div className="text-[11px] text-neutral-500 -mt-0.5">Orchestration • {isConnected ? 'Online' : 'Offline'}</div>
              </div>
            </div>
          </header>

          {/* Messages area mimic (empty) */}
          <div className="flex-1 overflow-y-auto bg-white relative z-0" />

          {/* Bottom input - same as chat composer (matches AgentChat) */}
          <footer className="shrink-0 border-t border-neutral-200 bg-white px-6 py-6">
            <div className="">
              <div className="rounded-3xl border border-neutral-200 bg-white shadow-sm">
                {/* Top textarea row */}
                <div className="px-5 pt-5 pb-2">
                  <textarea
                    className="w-full min-h-[120px] py-3 outline-none text-[17px] placeholder:text-neutral-400 resize-none"
                    placeholder={EXACT_TRIGGER}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
                  />
                </div>
                {/* Controls row */}
                <div className="flex items-center justify-between px-4 pb-4 pt-3">
                  <div className="flex items-center gap-2">
                    <button className="w-10 h-10 grid place-items-center rounded-xl border border-neutral-200 hover:bg-neutral-50" aria-label="Add">
                      <Plus className="w-4 h-4 text-neutral-700" />
                    </button>
                    <button className="w-10 h-10 grid place-items-center rounded-xl border border-neutral-200 hover:bg-neutral-50" aria-label="Settings">
                      <SlidersHorizontal className="w-4 h-4 text-neutral-700" />
                    </button>
                    <button className="h-10 px-3 rounded-xl border border-neutral-200 hover:bg-neutral-50 inline-flex items-center gap-2" aria-label="Research">
                      <SearchIcon className="w-4 h-4 text-neutral-700" />
                      <span className="text-sm text-neutral-800">Research</span>
                    </button>
                  </div>
                  <div className="flex items-center gap-2">
                    <button className="h-10 px-3 rounded-xl border border-neutral-200 hover:bg-neutral-50 inline-flex items-center gap-1" aria-label="Model selector">
                      <span className="text-sm text-neutral-800 hidden sm:inline">Claude Opus 4</span>
                      <ChevronDown className="w-4 h-4 text-neutral-500" />
                    </button>
                    <button className="w-11 h-11 grid place-items-center rounded-xl bg-indigo-600 text-white hover:bg-indigo-700" onClick={handleSend} aria-label="Send message">
                      <SendHorizonal className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </footer>
        </div>
        )}

        {/* Screen 2: Orchestration dashboards */}
        {demoUnlocked && !isLoading && (
          <div className="absolute inset-0 pt-[72px] pb-[136px] overflow-y-auto">
            <div className="max-w-7xl mx-auto p-8 space-y-8">
              {/* Trigger banner */}
              <div className="flex items-center gap-3 text-sm">
                <div className="px-3 py-1.5 rounded-full bg-neutral-100 border border-neutral-200 text-neutral-700">{triggerMessage}</div>
                <span className="text-xs text-neutral-500">triggered this workspace</span>
              <button className="ml-auto text-xs px-3 py-1.5 rounded-lg border border-neutral-200 hover:bg-neutral-50" onClick={onOpenWorkflowForm}>Open workflows</button>
            </div>

            {/* Flow content */}
            {websiteFlow !== 'idle' ? (
              <>
                <div className="rounded-3xl border border-neutral-200 bg-white shadow-sm p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <Palette className="w-4 h-4 text-neutral-600" />
                    <div className="font-semibold">
                      {websiteFlow === 'loading' ? 'Spinning up your website with Edith…' : 'Website staged'}
                    </div>
                  </div>
                  <div className="space-y-4">
                    {WEBSITE_LOADING_STEPS.map((s, i) => (
                      <div key={s} className={`flex items-center gap-3 ${i > webLoadIndex && websiteFlow === 'loading' ? 'opacity-50' : ''}`}>
                        <div className={`w-36 h-2 rounded bg-neutral-100 overflow-hidden`}>
                          <div className={`h-full bg-indigo-600 transition-transform origin-left ${i < webLoadIndex || websiteFlow === 'ready' ? '!scale-x-100' : 'scale-x-0'}`}></div>
                        </div>
                        <div className="text-sm text-neutral-700">{s}</div>
                      </div>
                    ))}
                  </div>
              </div>

                {websiteFlow === 'ready' && (
                  <div className="fixed top-4 right-4 z-20 rounded-2xl border border-neutral-200 bg-white shadow-lg p-4 w-[320px]">
                    <div className="flex items-start gap-3">
                      <img src="/Ed1th copy.png" alt="Edith" className="w-10 h-10 rounded-full object-cover" />
                      <div className="flex-1">
                        <div className="font-semibold leading-tight">Incoming call from Edith</div>
                        <div className="text-sm text-neutral-500">Website demo is ready</div>
                      </div>
                    </div>
                    <div className="mt-3 grid grid-cols-2 gap-2">
                      <button
                        className="rounded-lg bg-indigo-600 text-white py-2 hover:bg-indigo-700"
                        onClick={() => { onOpenWebsiteDemo(); setWebsiteFlow('idle') }}
                      >
                        Open demo
                      </button>
                      <button
                        className="rounded-lg border border-neutral-300 py-2 hover:bg-neutral-50"
                        onClick={() => setWebsiteFlow('idle')}
                      >
                        Dismiss
                      </button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <>
              <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                <div className="xl:col-span-2 rounded-3xl border border-neutral-200 bg-white shadow-sm p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <Activity className="w-4 h-4 text-neutral-600" />
                    <div className="font-semibold">Market analysis summary</div>
                  </div>
                  
                  {/* Opportunity Score and Strategy */}
                  {marketData && (
                    <div className="mb-4 p-4 bg-neutral-50 rounded-xl">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <div className="text-lg font-semibold text-neutral-800">
                            Opportunity Score: {marketData.market_opportunity_score || 0}%
                          </div>
                          <div className="text-sm text-neutral-600 mt-1">
                            {marketData.recommended_strategy || 'Strategic analysis pending'}
                          </div>
                        </div>
                        <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                          (marketData.market_opportunity_score || 0) >= 70 
                            ? 'bg-emerald-100 text-emerald-700' 
                            : (marketData.market_opportunity_score || 0) >= 50
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-rose-100 text-rose-700'
                        }`}>
                          {(marketData.market_opportunity_score || 0) >= 70 ? 'High Potential' : 
                           (marketData.market_opportunity_score || 0) >= 50 ? 'Moderate' : 'Challenging'}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  <MarketDataDisplay marketData={marketData} />
                </div>

                <div className="space-y-4">
                    <button className="group w-full rounded-3xl border border-neutral-200 bg-white shadow-sm p-5 hover:bg-neutral-50 cursor-pointer" onClick={startWebsiteFlow}>
                      <div className="flex items-center gap-4">
                        <img src="/Ed1th copy.png" alt="Edith" className="w-10 h-10 rounded-full object-cover" />
                        <div className="flex-1 text-left">
                    <div className="font-medium">Work with Edith to create a website?</div>
                    <div className="text-sm text-neutral-500">I can spin up a landing page and capture leads.</div>
                        </div>
                        <ArrowRight className="w-5 h-5 text-neutral-400 transition-transform group-hover:translate-x-0.5 group-hover:text-neutral-600" />
                      </div>
                  </button>
                    <button className="group w-full rounded-3xl border border-neutral-200 bg-white shadow-sm p-5 hover:bg-neutral-50 cursor-pointer">
                      <div className="flex items-center gap-4">
                        <img src="/Alfred copy.png" alt="Alfred" className="w-10 h-10 rounded-full object-cover" />
                        <div className="flex-1 text-left">
                    <div className="font-medium">Work with Alfred to evaluate PMF?</div>
                    <div className="text-sm text-neutral-500">We'll interview locals and validate pricing.</div>
                        </div>
                        <ArrowRight className="w-5 h-5 text-neutral-400 transition-transform group-hover:translate-x-0.5 group-hover:text-neutral-600" />
                      </div>
                  </button>
                </div>
              </div>

              {/* Middle row */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                  {(logoReady || brandingData) && (
                <div className="rounded-3xl border border-neutral-200 bg-white shadow-sm p-6">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Palette className="w-4 h-4 text-neutral-600" />
                      <div className="font-semibold">
                        {brandingData ? 'Brand identity created' : 'Logo generated'}
                      </div>
                    </div>
                    {brandingData && !logoData?.logo_url && (
                      <button 
                        onClick={generateLogo}
                        disabled={isGeneratingLogo || !selectedDomain}
                        className="px-3 py-1.5 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:bg-neutral-300 disabled:cursor-not-allowed"
                      >
                        {isGeneratingLogo ? 'Generating...' : 'Generate Logo'}
                      </button>
                    )}
                  </div>
                  <div className="flex items-center gap-5">
                    {logoData?.logo_url ? (
                      <LogoPreview src={logoData.logo_url} alt="Generated Logo" />
                    ) : (
                      <div className="w-24 h-24 rounded-2xl ring-1 ring-neutral-200 bg-neutral-50 grid place-items-center">
                        <div className="text-xs text-neutral-400">
                          {selectedDomain ? 'Ready to generate' : 'Select a domain first'}
                        </div>
                      </div>
                    )}
                    <div className="text-sm text-neutral-600">
                      {brandingData ? (
                        <div>
                          <div className="font-medium">{brandingData.brand_name}</div>
                          <div className="text-xs text-neutral-500 mt-1">{brandingData.tagline}</div>
                          {brandingData.colors && (
                            <div className="flex gap-1 mt-2">
                              {brandingData.colors.map((color: string, i: number) => (
                                <div key={i} className="w-4 h-4 rounded border" style={{backgroundColor: color}}></div>
                              ))}
                            </div>
                          )}
                        </div>
                      ) : (
                        'coppercrumb.png • MJ will iterate variations'
                      )}
                    </div>
                  </div>
                </div>
                  )}
                  <div className={`${(logoReady || brandingData) ? 'md:col-span-2' : 'md:col-span-3'} rounded-3xl border border-neutral-200 bg-white shadow-sm p-6`}>
                  <div className="flex items-center gap-2 mb-3">
                    <Globe className="w-4 h-4 text-neutral-600" />
                    <div className="font-semibold">Possible domains (GoDaddy)</div>
                  </div>
                  <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-3">
                    {domains.map((d) => {
                      const choice = domainChoice[d]
                      const borderCls = choice === 'accept' ? 'border-emerald-400' : choice === 'reject' ? 'border-rose-300' : 'border-neutral-200'
                      const textCls = choice === 'accept' ? 'text-emerald-700' : choice === 'reject' ? 'text-rose-700' : 'text-neutral-800'
                      return (
                          <div key={d} className={`rounded-xl border ${borderCls} px-3 py-2 text-sm flex items-start justify-between gap-3 hover:bg-neutral-50`}>
                            <span className={`${textCls} break-words min-w-0`}>{d}</span>
                          <div className="flex items-center gap-2 shrink-0">
                            <button
                              className={`w-7 h-7 rounded-full grid place-items-center border ${choice === 'accept' ? 'bg-emerald-50 border-emerald-400' : 'border-neutral-300 hover:bg-neutral-100'}`}
                              aria-label={`Accept ${d}`}
                              title={`Accept ${d}`}
                              onClick={() => {
                                setDomainChoice((m) => ({ ...m, [d]: 'accept' }));
                                setSelectedDomain(d);
                              }}
                            >
                              <Check className={`w-4 h-4 ${choice === 'accept' ? 'text-emerald-600' : 'text-neutral-600'}`} />
                            </button>
                            <button
                              className={`w-7 h-7 rounded-full grid place-items-center border ${choice === 'reject' ? 'bg-rose-50 border-rose-300' : 'border-neutral-300 hover:bg-neutral-100'}`}
                              aria-label={`Reject ${d}`}
                              title={`Reject ${d}`}
                              onClick={() => setDomainChoice((m) => ({ ...m, [d]: 'reject' }))}
                            >
                              <X className={`w-4 h-4 ${choice === 'reject' ? 'text-rose-600' : 'text-neutral-600'}`} />
                            </button>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>

              {/* Bottom prompt */}
              <div className="rounded-3xl border border-neutral-200 bg-white shadow-sm p-6">
                <div className="text-neutral-800 font-semibold mb-3">What do you want to do next?</div>
                <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
                  <button className="rounded-xl border border-neutral-200 px-3 py-2 text-left hover:bg-neutral-50">Run neighborhood survey</button>
                  <button className="rounded-xl border border-neutral-200 px-3 py-2 text-left hover:bg-neutral-50">Design menu v1</button>
                  <button className="rounded-xl border border-neutral-200 px-3 py-2 text-left hover:bg-neutral-50">Shortlist roasters</button>
                  <button className="rounded-xl border border-neutral-200 px-3 py-2 text-left hover:bg-neutral-50">Create launch timeline</button>
                </div>
                <div className="rounded-2xl border border-neutral-200 bg-white flex items-center">
                  <input ref={inputRef} className="w-full px-4 py-3 outline-none" placeholder="Type an instruction for Jarvis…" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleSend()} />
                  <button className={`m-1 px-3 py-2 rounded-lg ${isListening ? 'bg-rose-600' : 'bg-neutral-200 hover:bg-neutral-300'} text-neutral-800`} onClick={toggleListening} aria-label="Voice input" title="Voice input"><Mic className="w-4 h-4" /></button>
                  <button className="m-1 px-3 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700" onClick={handleSend} aria-label="Send" title="Send"><SendHorizonal className="w-4 h-4" /></button>
                  </div>
                </div>
              </>
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
        { from: 'edith', text: `Great. I'll add "${value}" to the draft menu and prep a price test.` },
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
          <Route path="*" element={<DemoRouteContent onOpenWebsiteDemo={openWebsiteDemo} onOpenWorkflowForm={()=>setShowWorkflowForm(true)} />} />
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
