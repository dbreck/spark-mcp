# Spark.re MCP Server

Model Context Protocol server that connects Claude Desktop to Spark.re's real estate CRM API, enabling natural language queries and **write operations** for complete sales workflow automation.

## Project Overview

**Purpose:** Enable Claude to directly query, create, update, and analyze Spark.re CRM data through conversational interface
**Location:** `/Users/dannybreckenridge/spark-mcp`
**Development:** Built in Claude Code, tested in Claude Desktop
**Status:** Production-ready with full read/write/analytics capabilities

**Key Features:**
- 📖 **Read Operations**: Search contacts, view details, analyze projects, track interactions
- ✍️ **Write Operations**: Create/update contacts, log interactions, add notes
- 📊 **Analytics Operations**: AI-powered insights on lead sources, engagement patterns, cohort analysis
- 🔄 **Complete Workflows**: From lead capture → interaction logging → follow-up notes → performance analysis
- 🎯 **Sales-Focused**: Designed for real estate agents' daily tasks and management decisions
- ✨ **Automatic ID Enrichment**: Shows "Email Out" instead of "Type ID 17861", "Nicholle DiPinto" instead of "Team Member 7927"
- 📄 **Pagination Support**: Access all results beyond first page (100+ contacts, interactions, etc.)

## Stack

- **Language:** TypeScript
- **Runtime:** Node.js 18+
- **MCP SDK:** @modelcontextprotocol/sdk
- **Transport:** StdioServerTransport (for Claude Desktop)
- **API:** Spark.re REST API (Bearer token auth)

## Prerequisites

- Node.js 18 or higher
- npm or yarn
- Spark.re API key (obtain from Spark.re project settings)
- Claude Desktop app (for testing)

## Project Structure

```
spark-mcp/
├── docs/                   # Spark.re API documentation (reference material)
├── src/
│   ├── index.ts           # MCP server entry point
│   ├── tools/             # Tool handlers by category
│   │   ├── contacts.ts    # Contact search and management
│   │   ├── projects.ts    # Project listing and details
│   │   ├── interactions.ts # Interaction history
│   │   └── reports.ts     # Analytics and reporting
│   ├── api/
│   │   ├── client.ts      # Spark.re API client with auth
│   │   └── types.ts       # TypeScript types for API responses
│   └── utils/
│       ├── formatting.ts  # Response formatting for readability
│       └── errors.ts      # Error handling utilities
├── dist/                  # Compiled JavaScript (generated)
├── package.json
├── tsconfig.json
├── .env                   # API credentials (git-ignored)
├── .env.example           # Template for credentials
├── PATTERNS.md            # Implementation patterns and examples
└── README.md              # This file
```

## Quick Start

### Installation (Clone Existing Repo)

```bash
# Clone the repository
git clone <repo-url> spark-mcp
cd spark-mcp

# Install dependencies
npm install

# Create environment file
cp .env.example .env
# Edit .env and add your SPARK_API_KEY

# Build the project
npm run build

# Verify build
ls dist/  # Should see index.js and other compiled files
```

### Setup from Scratch (New Project)

### 1. Initialize Project

```bash
npm init -y
npm install @modelcontextprotocol/sdk dotenv
npm install -D typescript @types/node
```

### 2. Configure TypeScript

Create `tsconfig.json`:

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

### 3. Add Build Scripts

Update `package.json`:

```json
{
  "type": "module",
  "scripts": {
    "build": "tsc",
    "watch": "tsc --watch",
    "start": "node dist/index.js"
  }
}
```

### 4. Set Up Environment

Create `.env`:

```bash
SPARK_API_KEY=your_api_key_here
SPARK_API_BASE_URL=https://api.spark.re/v1
```

Create `.env.example` (for git):

```bash
SPARK_API_KEY=your_api_key_here
SPARK_API_BASE_URL=https://api.spark.re/v1
```

## Development Workflow

### Phase 1: Foundation (Build First)

1. **API Client** (`src/api/client.ts`)
   - Bearer token authentication
   - Request/response handling
   - Error management
   - See PATTERNS.md for implementation

2. **Server Setup** (`src/index.ts`)
   - MCP server initialization
   - StdioServerTransport setup
   - Tool registration scaffold
   - See PATTERNS.md for boilerplate

3. **Types** (`src/api/types.ts`)
   - TypeScript interfaces for API responses
   - Contact, Project, Interaction types
   - Check `/docs/api/` for field definitions

### Phase 2: Core Tools (Priority Order)

Implement these tools in order of value:

1. **search_contacts** - Search contacts by name, email, project, rating
2. **get_contact_details** - Full contact profile with interactions
3. **list_projects** - Active projects with basic stats
4. **get_project_analytics** - Detailed project metrics
5. **search_interactions** - Recent contact activity

Each tool needs:
- Tool definition in `ListToolsRequestSchema` handler
- Handler function in appropriate `/tools/*.ts` file
- Response formatting in `/utils/formatting.ts`
- Error handling using `/utils/errors.ts`

See PATTERNS.md for complete examples of each component.

### Phase 3: Formatting & Polish

1. **Response Formatting** (`src/utils/formatting.ts`)
   - Convert API JSON to readable markdown
   - Use tables, bullet points, headers
   - Format dates as relative ("2 days ago")
   - See PATTERNS.md for formatting functions

2. **Error Handling** (`src/utils/errors.ts`)
   - User-friendly error messages
   - Rate limit retry logic
   - Auth failure detection
   - See PATTERNS.md for error patterns

## API Documentation

Complete Spark.re API documentation is in `/docs/api/` and `/docs/knowledge-base/`.

**Key endpoints to implement:**
- `GET /contacts` - Contact search
- `GET /contacts/:id` - Contact details
- `GET /projects` - Project list
- `GET /projects/:id/analytics` - Project stats
- `GET /interactions` - Interaction history

Refer to documentation for:
- Request parameters
- Response structure
- Authentication headers
- Rate limits

## Implementation Guidelines

### Authentication Pattern

All requests require Bearer token:

```typescript
headers: {
  'Authorization': `Bearer ${process.env.SPARK_API_KEY}`,
  'Content-Type': 'application/json',
  'Accept': 'application/json'
}
```

### Tool Naming Convention

Use clear, action-oriented names:
- ✅ `search_contacts`, `get_project_analytics`, `list_projects`
- ❌ `contacts`, `getData`, `fetch`

### Response Format

Always format responses for readability:
- Use markdown (headers, bullets, tables)
- Format dates as relative ("3 days ago")
- Structure data logically (most important first)
- Keep responses concise but complete

**Bad:** Return raw JSON
**Good:** Format as structured text with context

See PATTERNS.md for formatting examples.

### Error Handling

Return helpful error messages:
- ✅ "Authentication failed. Please check your SPARK_API_KEY."
- ❌ "Error 401: Unauthorized"

Handle common scenarios:
- Missing API key
- Invalid credentials
- Rate limits (retry with backoff)
- Network timeouts
- Empty results

## Testing

### Build & Run

```bash
# Compile TypeScript
npm run build

# Test the server
node dist/index.js
```

### Configure Claude Desktop

Edit Claude Desktop config:
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

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

### Test in Claude Desktop

1. Restart Claude Desktop after config changes
2. Start a new conversation
3. Try queries like:
   - "Search for contacts named John"
   - "Show me analytics for project X"
   - "What interactions happened in the last 7 days?"

### Debugging Checklist

If tools don't work:
- [ ] Check `npm run build` completes without errors
- [ ] Verify API key is set in config
- [ ] Check Claude Desktop console for error messages
- [ ] Test API client directly (before MCP integration)
- [ ] Validate response formatting returns strings, not objects

## Reference Materials

- **PATTERNS.md** - Complete implementation examples and code patterns
- **docs/api/** - Spark.re API endpoint documentation  
- **docs/knowledge-base/** - Spark.re feature documentation
- **MCP SDK Docs** - https://modelcontextprotocol.io

## Development Notes

### For Claude Code

When building this project:

1. **Start with the foundation** - API client and server setup first
2. **Build incrementally** - One tool at a time, test each before moving on
3. **Reference PATTERNS.md** - Don't reinvent patterns, use the examples
4. **Check docs/api/** - Verify endpoint structure before implementing
5. **Format responses** - Always make output readable for humans
6. **Handle errors gracefully** - User-friendly messages, no stack traces
7. **Use TypeScript types** - Define interfaces for API responses
8. **Test after each tool** - Compile and verify it works

### Common Pitfalls to Avoid

- ❌ Returning raw JSON instead of formatted text
- ❌ Not handling missing environment variables
- ❌ Forgetting to check response.ok before parsing
- ❌ Using technical error messages instead of user-friendly ones
- ❌ Not testing in Claude Desktop after building
- ❌ Hardcoding API keys instead of using environment variables

## Sales Workflow Diagram

```
New Lead
   ↓
[create_update_contact] ──→ Contact Created (ID: 123)
   ↓
Initial Call/Meeting
   ↓
[log_interaction] ──→ Activity Logged
   ↓
Follow-up Notes
   ↓
[add_contact_note] ──→ Note Added
   ↓
[search_contacts] ──→ Review Contact History
   ↓
[get_contact_details] ──→ Full Profile with All Notes & Interactions
```

## Available Tools

### Read Operations (Query Data)

1. **search_contacts** - Find contacts by name, email, project, or rating (with pagination)
2. **get_contact_details** - Get full contact profile with interactions and notes
3. **list_projects** - List all projects with basic information (with pagination)
4. **get_project_details** - Get detailed project information
5. **search_interactions** - Search interaction history with auto-enriched names (with pagination)

### Write Operations (Modify Data)

6. **create_update_contact** - Create new contacts or update existing ones
7. **log_interaction** - Log calls, meetings, emails, and other touchpoints
8. **add_contact_note** - Add quick notes to contact records

### Analytics Operations (AI-Powered Insights)

9. **get_contacts_by_criteria** - Advanced filtering returning 25-100 contacts for pattern analysis (with pagination)
10. **get_interaction_summary** - Aggregate interaction data with auto-enriched names, cadence and engagement metrics (with pagination)
11. **get_lead_sources** - Marketing source performance with quality scores and ROI data

### Reference Data Operations (ID Mapping)

12. **list_interaction_types** - Get all interaction type definitions (e.g., "Phone Call", "Email Out")
13. **list_team_members** - Get all team members with ID → name mapping
14. **list_ratings** - Get all contact rating definitions (e.g., "Hot Lead", "Agent")

## Practical Sales Workflow Examples

### Example 1: Complete New Lead Workflow

A sales agent meets a potential buyer at an open house and wants to add them to the CRM:

```
User: "I just met Sarah Johnson at the Mira Mar open house. Her email is sarah.j@email.com
       and phone is 941-555-1234. She's interested in a 2-bedroom unit and found us through
       our website. Can you add her to the system?"

Claude uses create_update_contact:
- Creates contact with name, email, phone
- Sets project_id to Mira Mar (2855)
- Sets marketing_source to "Website"
- Returns contact ID: 8103687

User: "Great! I just had a 30-minute phone call with her to discuss floor plans.
       Can you log that?"

Claude uses log_interaction:
- contact_id: 8103687
- project_id: 2855
- interaction_type_id: 1 (Call)
- notes: "30-minute call discussing 2-bedroom floor plans"
- Returns interaction ID

User: "She mentioned she needs to close by March. Add a note about that."

Claude uses add_contact_note:
- contact_id: 8103687
- project_id: 2855
- note: "Needs to close by March - timeline critical"
- Returns confirmation
```

### Example 2: Update Existing Contact After Meeting

```
User: "Search for contact John Smith in Mira Mar"

Claude uses search_contacts:
- Returns: John Smith, ID: 8099234, Email: jsmith@example.com

User: "I just met with John. Update his phone to 941-555-9876 and log the meeting.
       We discussed pricing and he's very interested in the penthouse units."

Claude uses create_update_contact:
- contact_id: 8099234
- phone: "941-555-9876"
- Returns updated contact

Then uses log_interaction:
- contact_id: 8099234
- interaction_type_id: 3 (Meeting)
- notes: "Discussed pricing for penthouse units - very interested"
- Returns confirmation
```

### Example 3: Referral Lead from Agent

```
User: "Add a new contact - Mark Davis, agent at Coldwell Banker.
       Email: mdavis@coldwell.com, phone 941-555-4321.
       He's referring clients to Mira Mar."

Claude uses create_update_contact:
- first_name: "Mark"
- last_name: "Davis"
- email: "mdavis@coldwell.com"
- phone: "941-555-4321"
- agent: true
- marketing_source: "Agent Referral"
- project_id: 2855
- Returns contact ID: 8103690

User: "Log that I emailed him our commission structure and floor plans today."

Claude uses log_interaction:
- contact_id: 8103690
- interaction_type_id: 2 (Email)
- notes: "Sent commission structure and floor plans"
```

### Example 4: Follow-up Workflow

```
User: "Show me all contacts from Mira Mar who haven't been contacted in the last 30 days"

Claude uses search_contacts with project_id filter, then analyzes last_interaction_date

User: "Call Lisa Martinez from that list. Update her phone to 941-555-7777 and log
       that I left a voicemail about our new pricing incentives."

Claude:
1. Searches for Lisa Martinez
2. Updates her phone number (create_update_contact)
3. Logs the interaction (log_interaction with notes: "Left voicemail about new pricing incentives")
```

### Example 5: Bulk Activity Logging

```
User: "I attended the Sarasota Home Show yesterday and collected 5 leads. Let me add them:

       1. Robert Chen - robert@email.com, 941-555-0001
       2. Maria Garcia - maria.g@email.com, 941-555-0002
       3. David Kim - dkim@email.com, 941-555-0003
       4. Jennifer White - jwhite@email.com, 941-555-0004
       5. Carlos Rodriguez - crodriguez@email.com, 941-555-0005

       All from the Home Show, all interested in Mira Mar."

Claude uses create_update_contact 5 times:
- Creates each contact
- Sets marketing_source: "Home Show"
- Sets project_id: 2855
- Returns all 5 contact IDs

User: "Add a note to all of them that they visited our booth on October 9th."

Claude uses add_contact_note 5 times:
- Adds "Visited Mira Mar booth at Sarasota Home Show on October 9, 2025" to each contact
```

## AI-Powered Analytics Examples

### Example 6: Lead Source Performance Analysis

```
User: "Which marketing sources are bringing us the best quality leads?"

Claude uses get_lead_sources:
- project_id: 2855
- Returns analysis of all sources with quality scores

Output includes:
- Contact Quality Score (0-100) based on data completeness and engagement
- Volume metrics (total contacts per source)
- Engagement rates (% with interaction history)
- Recent activity trends (30-day engagement)

Claude analyzes and responds:
"Based on the data, your top 3 sources are:
1. Website (Quality: 87/100) - 45 contacts, 82% have full contact info
2. Referral (Quality: 92/100) - 23 contacts, highest engagement at 91%
3. Home Show (Quality: 71/100) - 67 contacts, but only 54% engaged

Recommendation: Referrals convert best but Website brings volume.
Consider nurturing Home Show leads more actively."
```

### Example 7: Follow-up Cadence Analysis

```
User: "What's our average follow-up time with leads? Are we contacting
       people quickly enough?"

Claude uses get_interaction_summary:
- project_id: 2855
- days_ago: 30
- Returns interaction patterns and timing analysis

Output includes:
- Average time between interactions: 4.2 days
- Median time between interactions: 2.8 days
- Interaction types breakdown (calls, emails, meetings)
- Team member activity distribution
- Daily activity timeline

Claude analyzes:
"Your team averages 4.2 days between follow-ups, but the median is 2.8 days,
suggesting some leads wait much longer.

Top performers:
- Team Member 7927: 45 interactions (38%)
- Team Member 7925: 32 interactions (27%)

Peak activity days: Monday-Tuesday. Fridays show 40% less activity.

Recommendation: Set 48-hour follow-up rule for new leads to match your
median performers."
```

### Example 8: Cohort Analysis by Registration Date

```
User: "Compare leads from September vs October. Are October leads better quality?"

Claude uses get_contacts_by_criteria twice:
1. created_after: "2025-09-01T00:00:00Z", created_before: "2025-09-30T23:59:59Z"
2. created_after: "2025-10-01T00:00:00Z", created_before: "2025-10-31T23:59:59Z"

Returns two datasets with:
- Summary statistics (email/phone completion rates)
- Source distribution per cohort
- Engagement metrics
- Full contact details for pattern analysis

Claude compares:
"September: 34 contacts, 76% have email, 45% engaged
October: 52 contacts, 85% have email, 62% engaged

October leads are higher quality:
- Better data completion (+9% emails)
- Higher engagement rate (+17%)
- More diverse sources (7 vs 4)

Key difference: October had 'Fall Home Show' source with 18 high-quality leads."
```

### Example 9: Agent vs Direct Buyer Analysis

```
User: "Do we get better engagement from agents or direct buyers?"

Claude uses get_contacts_by_criteria twice:
1. agent: true, project_id: 2855, limit: 100
2. agent: false, project_id: 2855, limit: 100

Returns both datasets with engagement metrics

Claude analyzes:
"Agents (67 contacts):
- 94% have interaction history
- Average 3.8 interactions per agent
- 88% recent activity (30 days)

Direct Buyers (114 contacts):
- 58% have interaction history
- Average 2.1 interactions per buyer
- 42% recent activity (30 days)

Agents are 62% more engaged but represent only 37% of database.
Direct buyers need more nurturing - 48 have never been contacted."
```

### Example 10: Interaction Type Effectiveness

```
User: "Which interaction types correlate with more engaged leads -
       calls or emails?"

Claude uses get_interaction_summary:
- project_id: 2855
- days_ago: 60
- Returns breakdown by interaction type

Output shows:
- Type ID 17863 (Calls): 127 interactions, 45 unique contacts
- Type ID 17988 (Emails): 89 interactions, 62 unique contacts
- Type ID 17987 (Meetings): 34 interactions, 28 unique contacts

Claude calculates:
"Interaction patterns:
- Calls: 2.8 interactions per contact (high intensity)
- Emails: 1.4 interactions per contact (broadcast approach)
- Meetings: 1.2 interactions per contact (conversion stage)

Contacts with 2+ calls have 3x higher subsequent engagement.
Email-only contacts drop off after 45 days.

Recommendation: Use emails for initial reach, follow up with calls
within 48 hours for serious leads."
```

### Example 11: Time-Based Pattern Analysis

```
User: "Are leads added on weekends different from weekday leads?"

Claude uses get_contacts_by_criteria:
- Returns large dataset (75 contacts)
- Includes full timeline and source data

Claude analyzes creation timestamps:
"Weekend leads (Sat-Sun): 18 contacts
- 89% from 'Website' source
- 72% request callback (high intent)
- 61% convert to meetings

Weekday leads: 57 contacts
- More diverse sources (7 different)
- 45% request callback
- 34% convert to meetings

Weekend leads show 79% higher conversion intent.

Recommendation: Set up weekend lead alerts - these are hot prospects
researching on their own time."
```

### Example 12: Data Quality Audit

```
User: "How many of our leads are missing critical contact information?"

Claude uses get_contacts_by_criteria:
- project_id: 2855
- limit: 100
- Returns full dataset with completeness metrics

Output shows:
- 100 contacts analyzed
- 82% have email (82 contacts)
- 67% have phone (67 contacts)
- 54% have both email AND phone (54 contacts)

Claude identifies:
"Data quality issues:
- 18 contacts with NO email (can't reach)
- 33 contacts with NO phone (can't call)
- 46 contacts missing email OR phone

15 contacts have NO contact method at all.

These 15 incomplete records:
[Lists specific contact IDs]

Recommendation: Priority cleanup - get phone numbers for the 15 no-email
contacts, they're likely from walk-ins or events."
```

## Quick Reference: Common Tasks

| Task | Tool to Use | Required Fields |
|------|-------------|-----------------|
| Add new lead | `create_update_contact` | first_name, last_name, email, project_id |
| Update contact info | `create_update_contact` | contact_id + fields to update |
| Log a phone call | `log_interaction` | contact_id, project_id, interaction_type_id (1=Call) |
| Log a meeting | `log_interaction` | contact_id, project_id, interaction_type_id (3=Meeting) |
| Log an email sent | `log_interaction` | contact_id, project_id, interaction_type_id (2=Email) |
| Add quick note | `add_contact_note` | contact_id, project_id, note |
| Find a contact | `search_contacts` | query (name/email) |
| View contact history | `get_contact_details` | contact_id |

## Analytics Quick Reference

| Analysis Need | Tool to Use | Key Parameters |
|---------------|-------------|----------------|
| Source performance | `get_lead_sources` | project_id, min_contact_count |
| Follow-up cadence | `get_interaction_summary` | project_id, days_ago |
| Cohort comparison | `get_contacts_by_criteria` | created_after, created_before |
| Data quality audit | `get_contacts_by_criteria` | has_email, project_id |
| Agent vs buyer analysis | `get_contacts_by_criteria` | agent=true/false |
| Engagement patterns | `get_interaction_summary` | interaction_type_id, days_ago |
| Rating effectiveness | `get_contacts_by_criteria` | rating_id, project_id |
| Recent leads analysis | `get_contacts_by_criteria` | created_after, days_ago |

## Finding Interaction Type IDs

Interaction type IDs vary by Spark project. Common patterns:
- **1** = Phone Call
- **2** = Email
- **3** = Meeting
- **4** = Note/Comment

To find your project's specific IDs:
```
User: "Show me recent interactions from Mira Mar"
Claude uses search_interactions with project_id: 2855
Returns list showing interaction_type_id values used in your project
```

## Success Criteria

The MCP server is complete when:

- [x] TypeScript compiles without errors
- [x] All 11 tools are implemented (5 read + 3 write + 3 analytics)
- [x] Responses are formatted as readable text (not JSON)
- [x] Errors return helpful messages
- [x] Works in Claude Desktop conversations
- [x] Can answer queries like "Show me hot leads from Mira Mar"
- [x] Can create contacts, log interactions, and add notes
- [x] Supports complete sales workflow from lead to follow-up
- [x] Can perform AI-powered analytics on large datasets
- [x] Provides actionable insights from CRM data
- [x] API authentication works correctly
- [x] Rate limits are handled gracefully

## Support

- Spark.re API Issues: support@spark.re
- MCP Protocol Questions: https://github.com/modelcontextprotocol
- Project Issues: Check error logs in Claude Desktop console

## License

Private project for Clear PH / Mira Mar client work.
