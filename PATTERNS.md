# Spark.re MCP Server Implementation Patterns

## File Structure

```
spark-mcp/
├── docs/                          # Spark.re API documentation
│   ├── api/
│   └── knowledge-base/
├── src/
│   ├── index.ts                   # MCP server entry point
│   ├── tools/
│   │   ├── contacts.ts            # Contact-related tools
│   │   ├── projects.ts            # Project-related tools
│   │   ├── interactions.ts        # Interaction tools
│   │   └── reports.ts             # Analytics/reporting tools
│   ├── api/
│   │   ├── client.ts              # Spark.re API client
│   │   └── types.ts               # API response types
│   └── utils/
│       ├── formatting.ts          # Response formatting helpers
│       └── errors.ts              # Error handling utilities
├── package.json
├── tsconfig.json
├── .env.example
├── README.md
└── PATTERNS.md                    # This file
```

## Environment Setup

### .env.example
```bash
SPARK_API_KEY=your_api_key_here
SPARK_API_BASE_URL=https://api.spark.re/v1
```

### package.json
```json
{
  "name": "spark-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "build": "tsc",
    "watch": "tsc --watch",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "latest",
    "dotenv": "^16.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0"
  }
}
```

### tsconfig.json
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

## Spark.re API Structure & Endpoint Patterns

### Critical Endpoint Discoveries (v1.5.1)

**Naming Convention:**
- Spark API uses **dashes** in endpoint names, NOT underscores
- ✅ Correct: `/team-members`, `/contact-ratings`, `/interaction-types`
- ❌ Wrong: `/team_members`, `/contact_ratings`, `/interaction_types`

**Resource Scope:**

1. **Account-Level Resources** (no project_id needed):
   - `/team-members` - All users/team members across the account
   - Returns all team members regardless of project
   - Example: Team Member 7927 "Nicholle DiPinto McKiernan"

2. **Project-Level Resources** (require project_id filter):
   - `/contact-ratings?project_id_eq={id}` - Ratings specific to a project
   - `/projects/{id}/interaction-types` - Interaction types for a project
   - Returns project-specific configurations

3. **Many-to-Many Resources**:
   - `/contacts` - Contacts can belong to multiple projects
   - **Limitation:** `project_id_eq` filter doesn't work reliably
   - Workaround: Use `/interactions?project_id_eq={id}` to get project contacts

**Endpoint Testing Results:**
```bash
# Team members (account-level) ✅
curl 'https://api.spark.re/v2/team-members?per_page=100'

# Ratings (project-level) ✅
curl 'https://api.spark.re/v2/contact-ratings?project_id_eq=2855&per_page=100'

# Interaction types (project-level) ✅
curl 'https://api.spark.re/v2/projects/2855/interaction-types'

# Contacts (many-to-many, filtering limited) ⚠️
curl 'https://api.spark.re/v2/contacts?per_page=100'
# Note: project_id not in response, exists only in detail view
```

**Auto-Enrichment Pattern:**
```typescript
// Correct implementation (v1.5.1+)
async getTeamMemberMap(project_id: number): Promise<Map<number, string>> {
  // Cache check
  if (this.teamMemberCache.has(project_id)) {
    return this.teamMemberCache.get(project_id)!;
  }

  // Use account-level endpoint with dash
  const members: any = await this.get(`/team-members?per_page=100`);

  const memberMap = new Map<number, string>();
  members.forEach((member: any) => {
    if (member.id) {
      const name = `${member.first_name || ''} ${member.last_name || ''}`.trim();
      memberMap.set(member.id, name);
    }
  });

  // Cache for session
  this.teamMemberCache.set(project_id, memberMap);
  return memberMap;
}
```

**Common Mistakes to Avoid:**
1. ❌ Using underscores: `/team_members` → Returns 404
2. ❌ Assuming project-level: `/projects/{id}/team_members` → Returns 404
3. ❌ Not caching: Repeated calls waste API quota
4. ❌ Filtering contacts by project_id: Doesn't work reliably

## Authentication Pattern

### API Client Setup
```typescript
// src/api/client.ts
export class SparkAPIClient {
  private baseURL: string;
  private apiKey: string;

  constructor() {
    this.baseURL = process.env.SPARK_API_BASE_URL || 'https://api.spark.re/v1';
    this.apiKey = process.env.SPARK_API_KEY || '';
    
    if (!this.apiKey) {
      throw new Error('SPARK_API_KEY environment variable is required');
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Spark API Error (${response.status}): ${errorText}`);
    }

    return response.json();
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}
```

## MCP Server Setup Pattern

### Basic Server Structure
```typescript
// src/index.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { SparkAPIClient } from "./api/client.js";
import dotenv from "dotenv";

dotenv.config();

const server = new Server(
  {
    name: "spark-re-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

const sparkApi = new SparkAPIClient();

// Tool registration and handlers go here...

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Spark.re MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
```

## Tool Registration Pattern

### Example: Contact Search Tool
```typescript
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "search_contacts",
      description: "Search for contacts in Spark.re CRM by name, email, project, or rating. Returns contact details including email, phone, project assignment, and last interaction date.",
      inputSchema: {
        type: "object",
        properties: {
          query: {
            type: "string",
            description: "Search term - can be name, email, or phone number"
          },
          project_id: {
            type: "string",
            description: "Optional: Filter by specific project ID"
          },
          rating: {
            type: "string",
            description: "Optional: Filter by lead rating (hot, warm, cold)"
          },
          limit: {
            type: "number",
            description: "Maximum number of results to return (default: 25)"
          }
        }
      }
    },
    {
      name: "get_contact_details",
      description: "Get full details for a specific contact by ID, including all interactions, notes, and project assignments",
      inputSchema: {
        type: "object",
        properties: {
          contact_id: {
            type: "string",
            description: "The unique ID of the contact"
          }
        },
        required: ["contact_id"]
      }
    },
    {
      name: "list_projects",
      description: "List all active projects in Spark.re with basic stats (total contacts, conversions, top sources)",
      inputSchema: {
        type: "object",
        properties: {
          status: {
            type: "string",
            description: "Filter by status: active, archived, all (default: active)"
          }
        }
      }
    },
    {
      name: "get_project_analytics",
      description: "Get detailed analytics for a specific project including conversion rates, lead sources, and registration trends",
      inputSchema: {
        type: "object",
        properties: {
          project_id: {
            type: "string",
            description: "The unique ID of the project"
          },
          date_range: {
            type: "string",
            description: "Time period: last_7_days, last_30_days, last_90_days, all_time (default: last_30_days)"
          }
        },
        required: ["project_id"]
      }
    },
    {
      name: "search_interactions",
      description: "Search for contact interactions (calls, emails, meetings, notes) by contact, date range, or type",
      inputSchema: {
        type: "object",
        properties: {
          contact_id: {
            type: "string",
            description: "Optional: Filter by specific contact"
          },
          interaction_type: {
            type: "string",
            description: "Optional: Type (call, email, meeting, note)"
          },
          days_ago: {
            type: "number",
            description: "Optional: Show interactions from last N days (default: 30)"
          }
        }
      }
    }
  ]
}));
```

## Tool Execution Pattern

### Main Handler with Error Management
```typescript
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  try {
    switch(name) {
      case "search_contacts":
        return await handleSearchContacts(args);
      
      case "get_contact_details":
        return await handleGetContactDetails(args);
      
      case "list_projects":
        return await handleListProjects(args);
      
      case "get_project_analytics":
        return await handleProjectAnalytics(args);
      
      case "search_interactions":
        return await handleSearchInteractions(args);
      
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return {
      content: [{
        type: "text",
        text: `Error executing ${name}: ${errorMessage}`
      }],
      isError: true
    };
  }
});
```

### Example Tool Handler
```typescript
// src/tools/contacts.ts
async function handleSearchContacts(args: any) {
  const { query = '', project_id, rating, limit = 25 } = args;
  
  // Build query params
  const params = new URLSearchParams();
  if (query) params.append('q', query);
  if (project_id) params.append('project_id', project_id);
  if (rating) params.append('rating', rating);
  params.append('limit', String(limit));
  
  // API call
  const contacts = await sparkApi.get(`/contacts?${params}`);
  
  // Format response
  const formatted = formatContactList(contacts);
  
  return {
    content: [{
      type: "text",
      text: formatted
    }]
  };
}
```

## Response Formatting Patterns

### Contact List Formatting
```typescript
// src/utils/formatting.ts
export function formatContactList(contacts: any[]): string {
  if (!contacts || contacts.length === 0) {
    return "No contacts found matching your criteria.";
  }
  
  let output = `Found ${contacts.length} contact(s):\n\n`;
  
  contacts.forEach((contact, index) => {
    output += `${index + 1}. **${contact.first_name} ${contact.last_name}**\n`;
    output += `   - Email: ${contact.email}\n`;
    if (contact.phone) {
      output += `   - Phone: ${contact.phone}\n`;
    }
    if (contact.project_name) {
      output += `   - Project: ${contact.project_name}\n`;
    }
    if (contact.rating) {
      output += `   - Rating: ${contact.rating}\n`;
    }
    if (contact.last_interaction) {
      output += `   - Last Contact: ${formatDate(contact.last_interaction)}\n`;
    }
    output += `   - ID: ${contact.id}\n`;
    output += '\n';
  });
  
  return output;
}
```

### Contact Details Formatting
```typescript
export function formatContactDetails(contact: any): string {
  let output = `# ${contact.first_name} ${contact.last_name}\n\n`;
  
  output += `## Contact Information\n`;
  output += `- Email: ${contact.email}\n`;
  if (contact.phone) output += `- Phone: ${contact.phone}\n`;
  if (contact.address) output += `- Address: ${contact.address}\n`;
  output += `- Rating: ${contact.rating || 'Not rated'}\n`;
  output += `- Source: ${contact.source || 'Unknown'}\n`;
  output += `- Created: ${formatDate(contact.created_at)}\n\n`;
  
  if (contact.projects && contact.projects.length > 0) {
    output += `## Projects\n`;
    contact.projects.forEach((proj: any) => {
      output += `- ${proj.name} (${proj.status})\n`;
    });
    output += '\n';
  }
  
  if (contact.recent_interactions && contact.recent_interactions.length > 0) {
    output += `## Recent Interactions\n`;
    contact.recent_interactions.slice(0, 5).forEach((interaction: any) => {
      output += `- ${formatDate(interaction.date)}: ${interaction.type} - ${interaction.notes}\n`;
    });
    output += '\n';
  }
  
  if (contact.notes) {
    output += `## Notes\n${contact.notes}\n`;
  }
  
  return output;
}
```

### Project Analytics Formatting
```typescript
export function formatProjectAnalytics(data: any): string {
  let output = `# ${data.project_name} Analytics\n\n`;
  
  output += `## Overview (${data.date_range})\n`;
  output += `- Total Contacts: ${data.total_contacts}\n`;
  output += `- New Contacts: ${data.new_contacts}\n`;
  output += `- Conversions: ${data.conversions} (${data.conversion_rate}%)\n`;
  output += `- Hot Leads: ${data.hot_leads}\n`;
  output += `- Warm Leads: ${data.warm_leads}\n\n`;
  
  if (data.sources && data.sources.length > 0) {
    output += `## Lead Sources\n`;
    data.sources.forEach((source: any) => {
      output += `- ${source.name}: ${source.count} (${source.percentage}%)\n`;
    });
    output += '\n';
  }
  
  if (data.registration_trend) {
    output += `## Registration Trend\n`;
    data.registration_trend.forEach((point: any) => {
      output += `- ${point.date}: ${point.count} registrations\n`;
    });
  }
  
  return output;
}
```

### Date Formatting Helper
```typescript
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
  
  return date.toLocaleDateString();
}
```

## Error Handling Patterns

### API Error Handler
```typescript
// src/utils/errors.ts
export class SparkAPIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public endpoint?: string
  ) {
    super(message);
    this.name = 'SparkAPIError';
  }
}

export function handleAPIError(error: any, context: string): string {
  if (error instanceof SparkAPIError) {
    if (error.statusCode === 401) {
      return `Authentication failed. Please check your SPARK_API_KEY environment variable.`;
    }
    if (error.statusCode === 403) {
      return `Permission denied. Your API key may not have access to ${context}.`;
    }
    if (error.statusCode === 404) {
      return `Resource not found. The ${context} may not exist or has been deleted.`;
    }
    if (error.statusCode === 429) {
      return `Rate limit exceeded. Please try again in a few moments.`;
    }
  }
  
  return `Failed to ${context}: ${error.message}`;
}
```

### Rate Limit Handling with Retry
```typescript
export async function fetchWithRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delayMs: number = 1000
): Promise<T> {
  let lastError: Error;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      
      // Only retry on rate limit errors
      if (error instanceof SparkAPIError && error.statusCode === 429) {
        if (attempt < maxRetries - 1) {
          await sleep(delayMs * Math.pow(2, attempt)); // Exponential backoff
          continue;
        }
      }
      
      // Don't retry other errors
      throw error;
    }
  }
  
  throw lastError!;
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

## Tool Naming Convention

### Good Examples
- `search_contacts` - Action-oriented, clear intent
- `get_contact_details` - Specific about what it retrieves
- `list_projects` - Descriptive of return type
- `get_project_analytics` - Clear scope and purpose
- `search_interactions` - Action + subject

### Bad Examples
- ❌ `contacts` - Too vague
- ❌ `project` - Not actionable
- ❌ `getData` - Generic, unclear
- ❌ `fetch` - Developer jargon
- ❌ `queryDB` - Implementation detail

## Testing Checklist

Before considering a tool complete:

- [ ] **Missing parameters** - Tool handles when optional params are omitted
- [ ] **Invalid parameters** - Returns helpful error for bad input types
- [ ] **Empty results** - Graceful message when no data found
- [ ] **Authentication failure** - Clear error about API key issues
- [ ] **Rate limit** - Proper retry logic or clear error message
- [ ] **Network errors** - Handles timeouts and connection issues
- [ ] **Response formatting** - Output is readable, not raw JSON
- [ ] **Works in Claude Desktop** - Actually test the integration
- [ ] **Error messages** - Non-technical users can understand them
- [ ] **Documentation** - README has example usage

## Claude Desktop Configuration

### config.json location
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Configuration Format
```json
{
  "mcpServers": {
    "spark-re": {
      "command": "node",
      "args": ["/Users/dannybreckenridge/spark-mcp/dist/index.js"],
      "env": {
        "SPARK_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Common API Endpoints Reference

Based on Spark.re API documentation:

- `GET /contacts` - Search contacts
- `GET /contacts/:id` - Get contact details
- `POST /contacts` - Create contact
- `PUT /contacts/:id` - Update contact
- `GET /projects` - List projects
- `GET /projects/:id` - Get project details
- `GET /projects/:id/analytics` - Project stats
- `GET /interactions` - Search interactions
- `GET /interactions/:id` - Get interaction details
- `GET /forms` - List registration forms
- `GET /forms/:id/submissions` - Form submissions
- `GET /reports/contacts` - Contact reports
- `GET /reports/sales` - Sales reports

Refer to `/Users/dannybreckenridge/spark-mcp/docs/` for complete endpoint documentation.

## Best Practices Summary

1. **Always validate inputs** before making API calls
2. **Format responses for humans** - use markdown, tables, bullet points
3. **Handle errors gracefully** - return helpful messages, not stack traces
4. **Reference docs** - Check actual API structure in `/docs/`
5. **Keep tool descriptions clear** - Write for non-technical users
6. **Test incrementally** - Build one tool at a time, test thoroughly
7. **Use TypeScript types** - Define interfaces for API responses
8. **Log to stderr** - Keep stdout clean for MCP protocol
9. **Fail fast** - Validate env vars and config at startup
10. **Document everything** - Future you will thank present you
