# Spark.re MCP Server - Complete Tool Reference

**Version:** 1.2.0
**Last Updated:** 2025-10-10

This document provides a comprehensive reference for all 11 tools available in the Spark.re MCP server.

---

## Read Operations (5 tools)

### 1. search_contacts

**Purpose:** Find contacts by name, email, project, or rating

**Parameters:**
- `query` (string, optional) - Search term (name, email, or phone)
- `project_id` (number, optional) - Filter by project
- `rating_id` (number, optional) - Filter by lead rating
- `limit` (number, optional) - Max results (default: 25)

**Returns:** List of contacts with email, phone, project, rating, last interaction date

**Example:**
```
"Search for contacts named Sarah in Mira Mar"
```

---

### 2. get_contact_details

**Purpose:** Get complete contact profile with full history

**Parameters:**
- `contact_id` (number, required) - The contact's unique ID

**Returns:** Full contact information including:
- Contact info (email, phone, address)
- Project assignment
- All notes (with dates and authors)
- Source/rating

**Example:**
```
"Show me all details for contact 8103687"
```

---

### 3. list_projects

**Purpose:** List all projects with basic information

**Parameters:**
- `limit` (number, optional) - Max results (default: 25)

**Returns:** List of projects with name, type, sales stage, location, ID

**Example:**
```
"Show me all active projects"
```

---

### 4. get_project_details

**Purpose:** Get detailed information for a specific project

**Parameters:**
- `project_id` (number, required) - The project's unique ID

**Returns:** Complete project details including:
- Type, sales stage, status
- Full address and location
- Statistics (contact count, inventory)
- Buildings
- Marketing info

**Example:**
```
"Get details for Mira Mar project (ID 2855)"
```

---

### 5. search_interactions

**Purpose:** Search interaction history by contact, type, or date

**Parameters:**
- `contact_id` (number, optional) - Filter by contact
- `interaction_type_id` (number, optional) - Filter by type
- `days_ago` (number, optional) - Last N days (default: 30)
- `limit` (number, optional) - Max results (default: 25)

**Returns:** List of interactions with type, date, notes, contact ID

**Example:**
```
"Show me all interactions from the last 7 days"
```

---

## Write Operations (3 tools)

### 6. create_update_contact

**Purpose:** Create new contact or update existing one

**Parameters:**
- `contact_id` (number, optional) - ID to update (omit to create new)
- `project_id` (number, required for new) - Project assignment
- `first_name` (string, required) - First name
- `last_name` (string, required) - Last name
- `email` (string, required) - Email address
- `phone` (string, optional) - Primary phone
- `mobile_phone` (string, optional) - Mobile phone
- `work_phone` (string, optional) - Work phone
- `address_line_1` (string, optional) - Street address
- `address_line_2` (string, optional) - Apt/unit
- `city` (string, optional) - City
- `province` (string, optional) - State/province
- `postcode` (string, optional) - ZIP/postal code
- `country_iso` (string, optional) - Country code (USA, CAN, etc.)
- `agent` (boolean, optional) - Mark as real estate agent
- `marketing_source` (string, optional) - Lead source

**Returns:** Created/updated contact with confirmation and next steps

**Example:**
```
"Add Sarah Johnson - email sarah.j@email.com, phone 941-555-1234,
 found us through Website, for Mira Mar project"
```

---

### 7. log_interaction

**Purpose:** Log calls, meetings, emails, and other touchpoints

**Parameters:**
- `contact_id` (number, required) - Contact this relates to
- `project_id` (number, required) - Project context
- `interaction_type_id` (number, required) - Type of interaction
- `timestamp` (string, optional) - When it occurred (ISO 8601)
- `notes` (string, optional) - Details about the interaction

**Returns:** Confirmation with interaction ID and details

**Example:**
```
"Log a call with contact 8103687 about floor plans"
```

**Note:** Interaction type IDs vary by project. Common: 1=Call, 2=Email, 3=Meeting

---

### 8. add_contact_note

**Purpose:** Add quick note to contact record

**Parameters:**
- `contact_id` (number, required) - Contact to add note to
- `project_id` (number, required) - Project context
- `note` (string, required) - Note content

**Returns:** Confirmation that note was added

**Example:**
```
"Add note to contact 8103687: Needs to close by March - timeline critical"
```

---

## Analytics Operations (3 tools)

### 9. get_contacts_by_criteria

**Purpose:** Advanced filtering for batch analysis (25-100 contacts)

**Parameters:**
- `project_id` (number, optional) - Filter by project
- `rating_id` (number, optional) - Filter by rating
- `registration_source_id` (number, optional) - Filter by source
- `agent` (boolean, optional) - Filter agents vs buyers
- `created_after` (string, optional) - Date range start (ISO 8601)
- `created_before` (string, optional) - Date range end (ISO 8601)
- `has_email` (boolean, optional) - Must have email
- `limit` (number, optional) - Max results (default: 50, max: 100)

**Returns:** Dataset with:
- Summary statistics (completion rates, engagement)
- Source distribution
- Timeline by month
- Full contact details for each record

**Use Cases:**
- Cohort analysis (compare time periods)
- Data quality audits
- Agent vs buyer analysis
- Rating effectiveness studies

**Example:**
```
"Get all contacts from September 2025 to compare with October"
```

---

### 10. get_interaction_summary

**Purpose:** Aggregate interaction data for pattern analysis

**Parameters:**
- `project_id` (number, optional) - Filter by project
- `contact_id` (number, optional) - Analyze specific contact
- `interaction_type_id` (number, optional) - Filter by type
- `days_ago` (number, optional) - Last N days (default: 30)
- `created_after` (string, optional) - Custom date range
- `limit` (number, optional) - Max raw records (default: 100)

**Returns:** Analysis with:
- Breakdown by interaction type (with percentages)
- Team member activity distribution
- Daily timeline (last 14 days)
- Contact engagement metrics
- **Follow-up cadence**: avg/median time between interactions
- Top 10 most engaged contacts

**Use Cases:**
- Follow-up timing optimization
- Team performance analysis
- Interaction type effectiveness
- Response time patterns

**Example:**
```
"What's our average follow-up time with leads in the last 30 days?"
```

---

### 11. get_lead_sources

**Purpose:** Marketing source performance and ROI analysis

**Parameters:**
- `project_id` (number, optional) - Filter by project
- `include_agent_sources` (boolean, optional) - Include agent leads (default: true)
- `min_contact_count` (number, optional) - Min contacts to show (default: 1)
- `days_ago` (number, optional) - Recent activity window

**Returns:** Analysis with:
- **Contact Quality Score** (0-100) per source
- Volume metrics (total contacts per source)
- Data completeness (% with email/phone)
- Engagement rates (% with interaction history)
- Recent activity (30-day engagement)
- Key insights: highest volume, quality, engagement

**Use Cases:**
- Marketing ROI analysis
- Source performance comparison
- Budget allocation decisions
- Lead quality assessment

**Example:**
```
"Which marketing sources bring us the best quality leads?"
```

---

## Tool Categories at a Glance

| Category | Tools | Primary Use |
|----------|-------|-------------|
| **Search & Lookup** | search_contacts, list_projects | Find specific records |
| **Details & History** | get_contact_details, get_project_details, search_interactions | Deep dive on records |
| **Data Entry** | create_update_contact, log_interaction, add_contact_note | Daily sales activities |
| **Analytics** | get_contacts_by_criteria, get_interaction_summary, get_lead_sources | Strategic decisions |

---

## Common Workflows

### New Lead to Follow-up
1. `create_update_contact` - Add the lead
2. `log_interaction` - Record initial call/meeting
3. `add_contact_note` - Add follow-up reminder
4. `get_contact_details` - Review full history

### Source Performance Review
1. `get_lead_sources` - See all sources ranked
2. `get_contacts_by_criteria` - Deep dive on top source
3. `get_interaction_summary` - Check engagement patterns

### Data Quality Audit
1. `get_contacts_by_criteria` (has_email: false) - Find incomplete records
2. `create_update_contact` - Fix missing data
3. `get_contacts_by_criteria` - Re-check completeness

---

## Version History

- **1.2.0** (2025-10-10): Added 3 analytics tools + bug fixes
- **1.1.0** (2025-10-10): Added 3 write operations
- **1.0.1** (2025-10-10): Fixed search and notes bugs
- **1.0.0** (2025-10-10): Initial release with 5 read tools
