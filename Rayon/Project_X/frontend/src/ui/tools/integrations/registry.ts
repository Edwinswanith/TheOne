import type { IntegrationPermission } from "../../../transport/types";
import { GOOGLE_MODEL_OPTIONS } from "../../../lib/integration-validation";

export type IntegrationField = {
  key: string;
  label: string;
  type: "text" | "password";
  placeholder?: string;
};

export type IntegrationCategory =
  | "LLM Providers"
  | "Web Search"
  | "Google Workspace"
  | "Microsoft"
  | "Communication"
  | "Productivity";

export type IntegrationDef = {
  id: string;
  name: string;
  icon: string;
  category: IntegrationCategory;
  description: string;
  authType: "oauth" | "apikey" | "both";
  fields: IntegrationField[];
  models?: string[];
  setupSteps: string[];
  permissions: IntegrationPermission[];
};

export const INTEGRATION_REGISTRY: IntegrationDef[] = [
  // ───────── LLM Providers ─────────
  {
    id: "openai",
    name: "OpenAI",
    icon: "Bot",
    category: "LLM Providers",
    description: "GPT-4o, o1, o3 language models",
    authType: "apikey",
    fields: [
      { key: "apiKey", label: "API Key", type: "password", placeholder: "sk-..." },
    ],
    models: [
      "gpt-4.1",
      "gpt-4.1-mini",
      "gpt-4.1-nano",
      "gpt-4o",
      "gpt-4o-mini",
      "gpt-4-turbo",
      "o1",
      "o1-mini",
      "o1-pro",
      "o3",
      "o3-mini",
      "o4-mini",
    ],
    setupSteps: [
      "Go to platform.openai.com → API Keys",
      "Create a new secret key",
      "Copy the API Key here",
    ],
    permissions: ["read"],
  },
  {
    id: "anthropic",
    name: "Anthropic / Claude",
    icon: "Brain",
    category: "LLM Providers",
    description: "Claude Opus, Sonnet, Haiku models",
    authType: "apikey",
    fields: [
      { key: "apiKey", label: "API Key", type: "password", placeholder: "sk-ant-..." },
    ],
    models: [
      "claude-opus-4-6",
      "claude-sonnet-4-6",
      "claude-haiku-4-5-20251001",
      "claude-3-5-sonnet-20241022",
      "claude-3-5-haiku-20241022",
      "claude-3-opus-20240229",
      "claude-3-sonnet-20240229",
      "claude-3-haiku-20240307",
    ],
    setupSteps: [
      "Go to console.anthropic.com → API Keys",
      "Create a new API key",
      "Copy the API Key here",
    ],
    permissions: ["read"],
  },
  {
    id: "google-ai",
    name: "Google AI / Gemini",
    icon: "Sparkles",
    category: "LLM Providers",
    description: "Gemini 2.5 stable and Gemini 3 preview models",
    authType: "apikey",
    fields: [
      { key: "apiKey", label: "API Key", type: "password" },
    ],
    models: [...GOOGLE_MODEL_OPTIONS],
    setupSteps: [
      "Go to aistudio.google.com → API Keys",
      "Create a new API key",
      "Copy the API Key here",
    ],
    permissions: ["read"],
  },
  {
    id: "groq",
    name: "Groq",
    icon: "Zap",
    category: "LLM Providers",
    description: "Ultra-fast LLaMA and Mixtral inference",
    authType: "apikey",
    fields: [
      { key: "apiKey", label: "API Key", type: "password" },
    ],
    models: [
      "llama-3.3-70b-versatile",
      "llama-3.1-70b-versatile",
      "llama-3.1-8b-instant",
      "llama3-70b-8192",
      "mixtral-8x7b-32768",
      "gemma2-9b-it",
      "gemma-7b-it",
    ],
    setupSteps: [
      "Go to console.groq.com → API Keys",
      "Create a new API key",
      "Copy the API Key here",
    ],
    permissions: ["read"],
  },
  {
    id: "mistral",
    name: "Mistral",
    icon: "Wind",
    category: "LLM Providers",
    description: "Mistral Large and Small models",
    authType: "apikey",
    fields: [
      { key: "apiKey", label: "API Key", type: "password" },
    ],
    models: [
      "mistral-large-latest",
      "mistral-medium-latest",
      "mistral-small-latest",
      "open-mistral-nemo",
      "codestral-latest",
    ],
    setupSteps: [
      "Go to console.mistral.ai → API Keys",
      "Create a new API key",
      "Copy the API Key here",
    ],
    permissions: ["read"],
  },
  {
    id: "grok",
    name: "Grok (xAI)",
    icon: "Zap",
    category: "LLM Providers",
    description: "xAI Grok language models",
    authType: "apikey",
    fields: [
      { key: "apiKey", label: "API Key", type: "password" },
    ],
    models: [
      "grok-3",
      "grok-3-mini",
      "grok-2",
      "grok-2-mini",
    ],
    setupSteps: [
      "Go to console.x.ai → API Keys",
      "Create a new API key",
      "Copy the API Key here",
    ],
    permissions: ["read"],
  },
  {
    id: "perplexity",
    name: "Perplexity",
    icon: "Search",
    category: "LLM Providers",
    description: "Sonar Pro and Sonar search-augmented models",
    authType: "apikey",
    fields: [
      { key: "apiKey", label: "API Key", type: "password" },
    ],
    models: [
      "sonar-pro",
      "sonar",
      "sonar-reasoning-pro",
      "sonar-reasoning",
    ],
    setupSteps: [
      "Go to perplexity.ai → API Settings",
      "Generate an API key",
      "Copy the API Key here",
    ],
    permissions: ["read"],
  },
  {
    id: "cohere",
    name: "Cohere",
    icon: "Layers",
    category: "LLM Providers",
    description: "Command R+ and Command R models",
    authType: "apikey",
    fields: [
      { key: "apiKey", label: "API Key", type: "password" },
    ],
    models: [
      "command-a-03-2025",
      "command-r-plus-08-2024",
      "command-r-08-2024",
      "command-r-plus",
      "command-r",
    ],
    setupSteps: [
      "Go to dashboard.cohere.com → API Keys",
      "Create a new API key",
      "Copy the API Key here",
    ],
    permissions: ["read"],
  },
  {
    id: "together",
    name: "Together AI",
    icon: "Users",
    category: "LLM Providers",
    description: "Open-source model hosting and inference",
    authType: "apikey",
    fields: [
      { key: "apiKey", label: "API Key", type: "password" },
    ],
    models: [
      "meta-llama/Llama-3.3-70B-Instruct-Turbo",
      "meta-llama/Llama-3.1-405B-Instruct-Turbo",
      "meta-llama/Llama-3.1-8B-Instruct-Turbo",
      "Qwen/Qwen2.5-72B-Instruct-Turbo",
      "mistralai/Mixtral-8x22B-Instruct-v0.1",
      "google/gemma-2-27b-it",
    ],
    setupSteps: [
      "Go to api.together.xyz → Settings → API Keys",
      "Create a new API key",
      "Copy the API Key here",
    ],
    permissions: ["read"],
  },

  // ───────── Web Search ─────────
  {
    id: "brave-search",
    name: "Brave Search",
    icon: "Search",
    category: "Web Search",
    description: "Privacy-focused web search API",
    authType: "apikey",
    fields: [
      { key: "apiKey", label: "API Key", type: "password" },
    ],
    setupSteps: [
      "Go to brave.com/search/api and sign up",
      "Create a new API key in your dashboard",
      "Copy the API Key here",
    ],
    permissions: ["read"],
  },
  {
    id: "perplexity-search",
    name: "Perplexity Search",
    icon: "Search",
    category: "Web Search",
    description: "AI-powered search via Perplexity API",
    authType: "apikey",
    fields: [
      { key: "apiKey", label: "API Key", type: "password" },
    ],
    setupSteps: [
      "Go to perplexity.ai → API Settings",
      "Generate an API key",
      "Copy the API Key here",
    ],
    permissions: ["read"],
  },
  {
    id: "serpapi",
    name: "SerpAPI",
    icon: "Search",
    category: "Web Search",
    description: "Search engine results page scraping API",
    authType: "apikey",
    fields: [
      { key: "apiKey", label: "API Key", type: "password" },
    ],
    setupSteps: [
      "Go to serpapi.com and create an account",
      "Find your API key in your account dashboard",
      "Copy the API Key here",
    ],
    permissions: ["read"],
  },
  {
    id: "serper",
    name: "Serper",
    icon: "Search",
    category: "Web Search",
    description: "Google Search results API",
    authType: "apikey",
    fields: [
      { key: "apiKey", label: "API Key", type: "password" },
    ],
    setupSteps: [
      "Go to serper.dev and create an account",
      "Generate an API key from your dashboard",
      "Copy the API Key here",
    ],
    permissions: ["read"],
  },
  {
    id: "google-custom-search",
    name: "Google Custom Search",
    icon: "Search",
    category: "Web Search",
    description: "Google Programmable Search Engine",
    authType: "apikey",
    fields: [
      { key: "apiKey", label: "API Key", type: "password" },
      { key: "searchEngineId", label: "Search Engine ID", type: "text", placeholder: "cx=..." },
    ],
    setupSteps: [
      "Go to programmablesearchengine.google.com and create an engine",
      "Enable the Custom Search API in Google Cloud Console",
      "Generate an API key under Credentials",
      "Copy the API Key and Search Engine ID here",
    ],
    permissions: ["read"],
  },
  {
    id: "bing-search",
    name: "Bing Search",
    icon: "Search",
    category: "Web Search",
    description: "Microsoft Bing Web Search API",
    authType: "apikey",
    fields: [
      { key: "apiKey", label: "API Key", type: "password" },
    ],
    setupSteps: [
      "Go to Azure Portal → Create a Bing Search resource",
      "Navigate to Keys and Endpoint",
      "Copy one of your API keys here",
    ],
    permissions: ["read"],
  },
  {
    id: "duckduckgo",
    name: "DuckDuckGo",
    icon: "Search",
    category: "Web Search",
    description: "Free privacy-focused web search (no API key needed)",
    authType: "apikey",
    fields: [],
    setupSteps: [
      "No setup required — DuckDuckGo search works without an API key",
    ],
    permissions: ["read"],
  },
  {
    id: "tavily",
    name: "Tavily",
    icon: "Search",
    category: "Web Search",
    description: "AI-optimized search API",
    authType: "apikey",
    fields: [
      { key: "apiKey", label: "API Key", type: "password" },
    ],
    setupSteps: [
      "Go to tavily.com and create an account",
      "Generate an API key from your dashboard",
      "Copy the API Key here",
    ],
    permissions: ["read"],
  },

  // ───────── Google Workspace ─────────
  {
    id: "google-meet",
    name: "Google Meet",
    icon: "Video",
    category: "Google Workspace",
    description: "Schedule and manage video meetings",
    authType: "oauth",
    fields: [
      { key: "clientId", label: "Client ID", type: "text", placeholder: "xxxx.apps.googleusercontent.com" },
      { key: "clientSecret", label: "Client Secret", type: "password" },
    ],
    setupSteps: [
      "Go to Google Cloud Console → APIs & Services → Credentials",
      "Create an OAuth 2.0 Client ID (Web application)",
      "Enable the Google Meet API in your project",
      "Copy the Client ID and Client Secret here",
    ],
    permissions: ["read", "write", "edit"],
  },
  {
    id: "google-docs",
    name: "Google Docs",
    icon: "FileText",
    category: "Google Workspace",
    description: "Create and edit documents",
    authType: "oauth",
    fields: [
      { key: "clientId", label: "Client ID", type: "text", placeholder: "xxxx.apps.googleusercontent.com" },
      { key: "clientSecret", label: "Client Secret", type: "password" },
    ],
    setupSteps: [
      "Go to Google Cloud Console → APIs & Services → Credentials",
      "Create an OAuth 2.0 Client ID (Web application)",
      "Add your redirect URI under Authorized redirect URIs",
      "Copy the Client ID and Client Secret here",
    ],
    permissions: ["read", "write", "edit"],
  },
  {
    id: "google-sheets",
    name: "Google Sheets",
    icon: "Table",
    category: "Google Workspace",
    description: "Read and write spreadsheets",
    authType: "oauth",
    fields: [
      { key: "clientId", label: "Client ID", type: "text", placeholder: "xxxx.apps.googleusercontent.com" },
      { key: "clientSecret", label: "Client Secret", type: "password" },
    ],
    setupSteps: [
      "Go to Google Cloud Console → APIs & Services → Credentials",
      "Create an OAuth 2.0 Client ID (Web application)",
      "Enable the Google Sheets API in your project",
      "Copy the Client ID and Client Secret here",
    ],
    permissions: ["read", "write", "edit"],
  },
  {
    id: "google-slides",
    name: "Google Slides",
    icon: "Presentation",
    category: "Google Workspace",
    description: "Create and edit presentations",
    authType: "oauth",
    fields: [
      { key: "clientId", label: "Client ID", type: "text", placeholder: "xxxx.apps.googleusercontent.com" },
      { key: "clientSecret", label: "Client Secret", type: "password" },
    ],
    setupSteps: [
      "Go to Google Cloud Console → APIs & Services → Credentials",
      "Create an OAuth 2.0 Client ID (Web application)",
      "Enable the Google Slides API in your project",
      "Copy the Client ID and Client Secret here",
    ],
    permissions: ["read", "write", "edit"],
  },
  {
    id: "google-drive",
    name: "Google Drive",
    icon: "HardDrive",
    category: "Google Workspace",
    description: "Access and manage files in Drive",
    authType: "oauth",
    fields: [
      { key: "clientId", label: "Client ID", type: "text", placeholder: "xxxx.apps.googleusercontent.com" },
      { key: "clientSecret", label: "Client Secret", type: "password" },
    ],
    setupSteps: [
      "Go to Google Cloud Console → APIs & Services → Credentials",
      "Create an OAuth 2.0 Client ID (Web application)",
      "Enable the Google Drive API in your project",
      "Copy the Client ID and Client Secret here",
    ],
    permissions: ["read", "write", "edit"],
  },

  // ───────── Microsoft ─────────
  {
    id: "microsoft-teams",
    name: "Microsoft Teams",
    icon: "Users",
    category: "Microsoft",
    description: "Send messages and manage channels",
    authType: "oauth",
    fields: [
      { key: "appId", label: "Application (Client) ID", type: "text" },
      { key: "appSecret", label: "Client Secret", type: "password" },
      { key: "tenantId", label: "Tenant ID", type: "text" },
    ],
    setupSteps: [
      "Go to Azure Portal → App registrations → New registration",
      "Under Certificates & secrets, create a new client secret",
      "Under API permissions, add Microsoft Graph permissions",
      "Copy the Application ID, Client Secret, and Tenant ID here",
    ],
    permissions: ["read", "write", "edit"],
  },
  {
    id: "microsoft-outlook",
    name: "Outlook",
    icon: "Mail",
    category: "Microsoft",
    description: "Read and send emails",
    authType: "oauth",
    fields: [
      { key: "appId", label: "Application (Client) ID", type: "text" },
      { key: "appSecret", label: "Client Secret", type: "password" },
      { key: "tenantId", label: "Tenant ID", type: "text" },
    ],
    setupSteps: [
      "Go to Azure Portal → App registrations → New registration",
      "Under Certificates & secrets, create a new client secret",
      "Under API permissions, add Mail.Read and Mail.Send",
      "Copy the Application ID, Client Secret, and Tenant ID here",
    ],
    permissions: ["read", "write", "edit"],
  },
  {
    id: "microsoft-calendar",
    name: "Microsoft Calendar",
    icon: "Calendar",
    category: "Microsoft",
    description: "Manage Outlook calendar events",
    authType: "oauth",
    fields: [
      { key: "appId", label: "Application (Client) ID", type: "text" },
      { key: "appSecret", label: "Client Secret", type: "password" },
      { key: "tenantId", label: "Tenant ID", type: "text" },
    ],
    setupSteps: [
      "Go to Azure Portal → App registrations → New registration",
      "Under Certificates & secrets, create a new client secret",
      "Under API permissions, add Calendars.ReadWrite",
      "Copy the Application ID, Client Secret, and Tenant ID here",
    ],
    permissions: ["read", "write", "edit"],
  },

  // ───────── Communication ─────────
  {
    id: "slack",
    name: "Slack",
    icon: "Hash",
    category: "Communication",
    description: "Post messages and manage workspaces",
    authType: "both",
    fields: [
      { key: "clientId", label: "Client ID", type: "text" },
      { key: "clientSecret", label: "Client Secret", type: "password" },
      { key: "botToken", label: "Bot User OAuth Token", type: "password", placeholder: "xoxb-..." },
      { key: "signingSecret", label: "Signing Secret", type: "password" },
    ],
    setupSteps: [
      "Go to api.slack.com/apps and create a new app",
      "Under Basic Information, note the Client ID and Client Secret",
      "Under OAuth & Permissions, add required bot scopes and install the app",
      "Copy the Client ID and Client Secret to sign in via OAuth, or paste the Bot Token directly",
    ],
    permissions: ["read", "write", "edit"],
  },
  {
    id: "telegram",
    name: "Telegram",
    icon: "Send",
    category: "Communication",
    description: "Send messages via Telegram bot",
    authType: "apikey",
    fields: [
      { key: "botToken", label: "Bot Token", type: "password" },
    ],
    setupSteps: [
      "Open Telegram and message @BotFather",
      "Send /newbot and follow the prompts",
      "Copy the bot token provided by BotFather here",
    ],
    permissions: ["read", "write"],
  },
  {
    id: "whatsapp",
    name: "WhatsApp",
    icon: "MessageCircle",
    category: "Communication",
    description: "Send messages via WhatsApp Business API",
    authType: "apikey",
    fields: [
      { key: "accessToken", label: "Access Token", type: "password" },
      { key: "phoneNumberId", label: "Phone Number ID", type: "text" },
    ],
    setupSteps: [
      "Go to Meta for Developers → WhatsApp → Getting Started",
      "Set up your WhatsApp Business account",
      "Generate a permanent access token",
      "Copy the Access Token and Phone Number ID here",
    ],
    permissions: ["read", "write"],
  },

  // ───────── Productivity ─────────
  {
    id: "notion",
    name: "Notion",
    icon: "BookOpen",
    category: "Productivity",
    description: "Read and write Notion pages and databases",
    authType: "both",
    fields: [
      { key: "clientId", label: "OAuth Client ID", type: "text" },
      { key: "clientSecret", label: "OAuth Client Secret", type: "password" },
      { key: "integrationToken", label: "Internal Integration Token", type: "password", placeholder: "secret_..." },
    ],
    setupSteps: [
      "Go to notion.so/my-integrations and create a new integration",
      "For OAuth: note the OAuth Client ID and Client Secret under Integration type → Public",
      "For internal use: copy the Internal Integration Token",
      "Share the relevant Notion pages with your integration",
    ],
    permissions: ["read", "write", "edit"],
  },
  {
    id: "linkedin",
    name: "LinkedIn",
    icon: "Linkedin",
    category: "Productivity",
    description: "Post updates and manage professional profile",
    authType: "oauth",
    fields: [
      { key: "clientId", label: "Client ID", type: "text" },
      { key: "clientSecret", label: "Client Secret", type: "password" },
    ],
    setupSteps: [
      "Go to linkedin.com/developers → Create App",
      "Under Auth, note the Client ID and Client Secret",
      "Add the required OAuth 2.0 scopes",
      "Copy the Client ID and Client Secret here",
    ],
    permissions: ["read", "write"],
  },
];

export const INTEGRATION_CATEGORIES: IntegrationCategory[] = [
  "LLM Providers",
  "Web Search",
  "Google Workspace",
  "Microsoft",
  "Communication",
  "Productivity",
];

export type IntegrationTabId = "llm" | "web-search" | "product-integrations";

export const INTEGRATION_TABS: { id: IntegrationTabId; label: string }[] = [
  { id: "llm", label: "LLM" },
  { id: "web-search", label: "Web Search" },
  { id: "product-integrations", label: "Product Integrations" },
];

export const INTEGRATION_TAB_CATEGORIES: Record<IntegrationTabId, IntegrationCategory[]> = {
  "llm": ["LLM Providers"],
  "web-search": ["Web Search"],
  "product-integrations": ["Google Workspace", "Microsoft", "Communication", "Productivity"],
};
