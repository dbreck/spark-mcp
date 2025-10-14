# Changelog

All notable changes to the Spark.re MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.0] - 2025-10-13

### Added
- **get_sales_funnel**: Sales pipeline analytics tool
  - Returns rating distribution for engaged contacts (contacts with interactions)
  - Calculates stage conversion rates (New → Hot, Hot → Warm, etc.)
  - Shows engagement rate (% of total contacts with interactions)
  - Calculates overall close rate and reservation conversion
  - Uses interaction-based workaround: fetches interactions → extracts contact IDs → batch fetches contacts → aggregates ratings
  - Supports time-based filtering (`days_ago` parameter to analyze last N days)
  - Caps at 1000 interactions (10 pages) for performance
  - Batches contact fetches in groups of 100 (API limit)
  - Properly uses `ratings[0].value` format discovered in v1.5.3

### Fixed
- **get_sales_funnel**: Fixed ratings not appearing in sales funnel analysis
  - **Root cause:** Spark API's `/contacts` list endpoint returns "light" contact data without `ratings`, `projects`, `notes`, `team_members`, and other nested fields
  - **Solution:** Changed from batch list endpoint to individual contact fetches using `/contacts/{id}` endpoint
  - Fetches contacts in batches of 10 concurrent requests for performance (e.g., 176 contacts = ~18 seconds)
  - Individual endpoint returns full contact data with 49 fields including ratings array
  - Added visible debug information in tool response showing:
    - Number of contacts with/without ratings
    - Sample contacts with ratings (showing actual rating values and colors)
    - Sample contacts without ratings (showing raw ratings field data)
    - Total rating categories found
  - Added handling for empty ratings with helpful error message
  - Now accurately displays rating distribution (Agent, Not Interested, Warm, etc.)

### Changed
- Updated tool count: 15 tools total (was 14)

## [1.5.3] - 2025-10-13

### Fixed
- **Contact rating display bug**: Contacts now correctly show their ratings instead of "Not rated"
  - Fixed `handleGetContactDetails()` (line 723-726) to read from `ratings` array
  - Fixed `formatContactsResponse()` (line 668-670) to read from `ratings` array
  - Root cause: Spark API returns ratings as an array of objects `[{id, value, color, position}]`, not as individual properties
  - Now properly extracts rating value from first element of ratings array

## [1.5.2] - 2025-10-11

### Fixed
- **CRITICAL: Interaction type endpoint corrected**
  - Fixed `getInteractionTypeMap()` to use correct account-level endpoint `/interaction-types` instead of non-existent `/projects/{id}/interaction-types`
  - Interaction types are account-wide, not project-specific
  - Cache remains keyed by project_id for consistency with existing architecture
  - Added `per_page=100` parameter to fetch all interaction types in one request

## [1.5.1] - 2025-10-11

### Fixed
- **CRITICAL: Auto-enrichment now working correctly**
  - Fixed `getTeamMemberMap()` to use correct endpoint `/team-members` (was using `/projects/{id}/team_members`)
  - Fixed `getInteractionTypeMap()` to use correct endpoint with dashes `/projects/{id}/interaction-types` (was using underscores)
  - Team members are account-level, not project-specific
- **list_team_members**: Now uses correct `/team-members` endpoint and returns all account team members
  - Was trying to extract from contacts, which failed
  - Now properly displays all team members with names, emails, and job titles
- **list_ratings**: Now uses correct `/contact-ratings` endpoint with proper filtering
  - Was trying to extract from contact details, which failed
  - Now directly fetches ratings with project_id filter

### Changed
- **list_team_members**: Updated output to clarify team members are account-wide, not project-specific
- All endpoint calls now use correct Spark API naming (dashes, not underscores)

### Documentation
- **PATTERNS.md**: Added comprehensive section on Spark.re API structure
  - Endpoint naming conventions (dashes vs underscores)
  - Resource scope (account-level vs project-level)
  - Auto-enrichment implementation patterns
  - Common mistakes and how to avoid them

### Known Limitations
- **Contacts and Projects**: The `/contacts` endpoint doesn't include `project_id` in list responses. Contacts belong to multiple projects via a many-to-many relationship. The `project_id_eq` filter may not work as expected. Use interactions filtering by project_id for project-specific contact analysis.

## [1.5.0] - 2025-10-11

### Added
- **Automatic ID Enrichment**: All tool responses now automatically show human-readable names
  - Added `getInteractionTypeMap()` to SparkAPIClient with session-based caching
  - Added `getTeamMemberMap()` to SparkAPIClient with session-based caching
  - In-memory Map-based caching eliminates redundant API calls for reference data

### Changed
- **search_interactions**: Now automatically enriches interaction type names and team member names
  - Shows "Email Out" instead of "Type 17861"
  - Shows "Nicholle DiPinto" instead of "Team Member 7927"
- **get_interaction_summary**: Automatically enriches all statistics
  - Interaction Types Breakdown shows "Email Out: 50 interactions (32%)" instead of "Type ID 17861: 50 interactions (32%)"
  - Activity by Team Member shows "Nicholle DiPinto: 40 interactions" instead of "Team Member 7927: 40 interactions"
- Updated package description to mention automatic ID enrichment

### Improved
- No more manual lookup steps required - enrichment happens automatically on every tool call
- Caching reduces API load by storing reference data mappings in memory for the session
- Graceful fallback: If enrichment fails, displays IDs as before

## [1.4.0] - 2025-10-10

### Added
- **Reference Data Tools** (3 new tools for ID-to-name mapping):
  - `list_interaction_types`: Get all interaction type definitions with ID → name mapping
    - Shows types like "Phone Call", "Email Out", "Meeting"
    - Results are cached as reference data changes infrequently
  - `list_team_members`: Get all team members for a project
    - Maps team_member_id to names (e.g., '7927' → 'Nicholle DiPinto')
    - Includes email and job title where available
  - `list_ratings`: Get all contact rating definitions
    - Shows ratings like "Hot Lead", "Warm", "Cold", "Agent"
    - Includes color codes for visual reference

### Changed
- Updated tool count: 14 tools total
- Package description now mentions ID-to-name mapping

## [1.3.0] - 2025-10-10

### Added
- **Pagination Support**: All list/search tools now support pagination
  - `search_contacts`: Added `page` parameter to access beyond first 100 results
  - `get_contacts_by_criteria`: Added `page` parameter for full dataset access
  - `search_interactions`: Added `page` parameter with pagination metadata
  - `get_interaction_summary`: Added `page` parameter for large datasets
  - `list_projects`: Added `page` parameter to access all projects
  - Pagination metadata includes: currentPage, totalPages, hasMore, nextPage
  - User guidance: Tools indicate when more results are available

### Changed
- All responses now show page information: "Page X of Y"
- Added footer guidance: "More results available! Use page=X to see the next page"

## [1.2.0] - 2025-10-10

### Added
- **Analytics Tools** (3 new tools for AI-powered insights):
  - `get_contacts_by_criteria`: Advanced filtering returning 25-100 contacts for batch analysis
    - Filter by rating, source, agent type, date ranges
    - Summary statistics with completion rates
    - Source distribution and timeline analysis
    - Formatted for AI pattern recognition
  - `get_interaction_summary`: Aggregate interaction data with engagement metrics
    - Breakdown by interaction type and team member
    - Daily activity timeline (last 14 days)
    - Follow-up cadence analysis (avg/median time between interactions)
    - Top 10 most engaged contacts
  - `get_lead_sources`: Marketing source performance analysis
    - Contact Quality Score (0-100) per source
    - Data completeness and engagement rates
    - Key insights: highest volume, quality, and engagement sources

### Fixed
- **get_contacts_by_criteria**: Fixed NaN% display when result set is empty (zero-division bug)
  - Added `safePercentage` helper function
  - Now shows "0%" instead of "NaN%" for all percentage calculations

## [1.1.0] - 2025-10-10

### Added
- **Write Operations** (3 new tools):
  - `create_update_contact`: Create new contacts or update existing ones
    - Support for all contact fields (name, email, phone, address, etc.)
    - Smart behavior: omit contact_id to create, include to update
  - `log_interaction`: Log calls, meetings, emails, and other sales touchpoints
    - Supports custom timestamps and notes
    - Tracks all interaction types
  - `add_contact_note`: Add quick notes to contact records
    - For observations, reminders, and important details

### Changed
- Updated README with 5 practical sales workflow examples
- Added sales workflow diagram
- Updated tool count: 8 tools (5 read + 3 write)

## [1.0.1] - 2025-10-10

### Fixed
- **search_contacts**: Fixed query parameter not working for specific names. Previously used incorrect `_cont_any[]` syntax which created AND logic across fields (first_name AND last_name AND email), causing zero results. Now makes 3 parallel API requests and merges results to implement proper OR logic.
  - Search "Brian" now finds "Brian Wacnik"
  - Search "Williams" now finds "Shaun Williams"
  - Deduplicates results by contact ID

- **get_contact_details**: Fixed notes displaying as `[object Object]`. Notes field is an object/array that wasn't being properly formatted. Now handles:
  - Arrays of note objects with date, text, and author
  - Single note objects
  - Plain text notes
  - Empty notes

### Changed
- Authorization header now uses correct Spark.re format: `Token token="..."` instead of `Bearer ...`

## [1.0.0] - 2025-10-10

### Added
- Initial release of Spark.re MCP Server
- 5 core tools: search_contacts, get_contact_details, list_projects, get_project_details, search_interactions
- Bearer token authentication
- TypeScript implementation with full type definitions
- Response formatting for readable output
