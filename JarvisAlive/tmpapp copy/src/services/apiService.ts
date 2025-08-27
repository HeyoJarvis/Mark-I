// REST API Service for Jarvis Agent System
export interface AgentMessageRequest {
  session_id: string;
  agent_id: string;
  message: string;
}

export interface AgentMessageResponse {
  success: boolean;
  response: string;
  agent_id: string;
  error?: string;
}

export interface Agent {
  agent_id: string;
  name: string;
  description: string;
  type: string;
  icon: string;
}

export interface SessionResponse {
  session_id: string;
}

export interface AgentsResponse {
  agents: Agent[];
}

export interface LogoGenerationRequest {
  session_id: string;
  brand_name: string;
  logo_prompt: string;
  colors: string[];
}

export interface LogoGenerationResponse {
  success: boolean;
  logo_url?: string;
  error?: string;
}

class ApiService {
  private baseUrl = 'http://localhost:8001'; // Bridge API server port
  private sessionId: string | null = null;

  async createSession(): Promise<string> {
    const response = await fetch(`${this.baseUrl}/api/sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: 'demo_user'
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to create session: ${response.statusText}`);
    }

    const data: SessionResponse = await response.json();
    this.sessionId = data.session_id;
    return data.session_id;
  }

  async getAgents(): Promise<Agent[]> {
    const response = await fetch(`${this.baseUrl}/api/agents`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch agents: ${response.statusText}`);
    }

    const data: AgentsResponse = await response.json();
    return data.agents;
  }

  async sendMessage(agentId: string, message: string): Promise<AgentMessageResponse> {
    if (!this.sessionId) {
      await this.createSession();
    }

    const request: AgentMessageRequest = {
      session_id: this.sessionId!,
      agent_id: agentId,
      message: message
    };

    const response = await fetch(`${this.baseUrl}/api/agent/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`Failed to send message: ${response.statusText}`);
    }

    const data: AgentMessageResponse = await response.json();
    return data;
  }

  async getSessionHistory(sessionId: string) {
    const response = await fetch(`${this.baseUrl}/api/sessions/${sessionId}/history`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch session history: ${response.statusText}`);
    }

    return response.json();
  }

  async generateLogo(brandName: string, logoPrompt: string, colors: string[]): Promise<LogoGenerationResponse> {
    if (!this.sessionId) {
      await this.createSession();
    }

    const request: LogoGenerationRequest = {
      session_id: this.sessionId!,
      brand_name: brandName,
      logo_prompt: logoPrompt,
      colors: colors
    };

    const response = await fetch(`${this.baseUrl}/api/generate-logo`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`Failed to generate logo: ${response.statusText}`);
    }

    const data: LogoGenerationResponse = await response.json();
    return data;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }
}

export const apiService = new ApiService(); 