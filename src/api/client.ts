/**
 * Spark.re API Client
 * Version 1.5.2 (debug logging) - Fixed interaction type endpoint - now uses /interaction-types instead of /projects/{id}/interaction-types
 * Handles authentication and HTTP requests to the Spark.re API
 */

import { APIError, PaginatedResponse } from './types.js';

export class SparkAPIClient {
  private baseURL: string;
  private apiKey: string;
  private interactionTypeCache: Map<number, Map<number, string>>; // project_id -> (type_id -> name)
  private teamMemberCache: Map<number, Map<number, string>>; // project_id -> (member_id -> name)

  constructor() {
    this.baseURL = process.env.SPARK_API_BASE_URL || 'https://api.spark.re/v2';
    this.apiKey = process.env.SPARK_API_KEY || '';
    this.interactionTypeCache = new Map();
    this.teamMemberCache = new Map();

    if (!this.apiKey) {
      throw new Error('SPARK_API_KEY environment variable is required');
    }
  }

  /**
   * Parse pagination info from Link header
   * Format: <url>; rel="first", <url>; rel="last", <url>; rel="next", <url>; rel="prev"
   */
  private parseLinkHeader(linkHeader: string | null): {
    first?: number;
    last?: number;
    next?: number;
    prev?: number;
  } {
    const links: any = {};

    if (!linkHeader) return links;

    // Parse each link relation
    const parts = linkHeader.split(',');
    for (const part of parts) {
      // Match patterns like: <https://api.spark.re/v2/contacts?page=2&per_page=5>; rel="next"
      const match = part.match(/<[^>]*[?&]page=(\d+)[^>]*>;\s*rel="(\w+)"/);
      if (match) {
        const [, pageNum, rel] = match;
        links[rel] = parseInt(pageNum, 10);
      }
    }

    return links;
  }

  /**
   * Make an authenticated request to the Spark.re API
   */
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Authorization': `Token token="${this.apiKey}"`,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `Spark API Error (${response.status}): ${errorText}`;

      // Provide user-friendly error messages
      if (response.status === 401) {
        errorMessage = 'Authentication failed. Please check your SPARK_API_KEY environment variable.';
      } else if (response.status === 403) {
        errorMessage = 'Permission denied. Your API key may not have access to this resource.';
      } else if (response.status === 404) {
        errorMessage = 'Resource not found. The requested item may not exist or has been deleted.';
      } else if (response.status === 429) {
        errorMessage = 'Rate limit exceeded. Please try again in a few moments.';
      }

      const error: APIError = {
        message: errorMessage,
        status: response.status
      };
      throw error;
    }

    return response.json();
  }

  /**
   * Make an authenticated request and return pagination metadata
   */
  private async requestWithPagination<T>(endpoint: string, options: RequestInit = {}): Promise<PaginatedResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Authorization': `Token token="${this.apiKey}"`,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `Spark API Error (${response.status}): ${errorText}`;

      // Provide user-friendly error messages
      if (response.status === 401) {
        errorMessage = 'Authentication failed. Please check your SPARK_API_KEY environment variable.';
      } else if (response.status === 403) {
        errorMessage = 'Permission denied. Your API key may not have access to this resource.';
      } else if (response.status === 404) {
        errorMessage = 'Resource not found. The requested item may not exist or has been deleted.';
      } else if (response.status === 429) {
        errorMessage = 'Rate limit exceeded. Please try again in a few moments.';
      }

      const error: APIError = {
        message: errorMessage,
        status: response.status
      };
      throw error;
    }

    const data = await response.json();
    const linkHeader = response.headers.get('link');
    const links = this.parseLinkHeader(linkHeader);

    return {
      data,
      pagination: {
        currentPage: this.extractPageFromUrl(endpoint),
        firstPage: links.first,
        lastPage: links.last,
        nextPage: links.next,
        prevPage: links.prev,
        hasMore: !!links.next,
        totalPages: links.last
      }
    };
  }

  /**
   * Extract page number from URL/endpoint
   */
  private extractPageFromUrl(url: string): number {
    const match = url.match(/[?&]page=(\d+)/);
    return match ? parseInt(match[1], 10) : 1;
  }

  /**
   * Perform a GET request
   */
  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  /**
   * Perform a GET request with pagination metadata
   */
  async getWithPagination<T>(endpoint: string): Promise<PaginatedResponse<T>> {
    return this.requestWithPagination<T>(endpoint, { method: 'GET' });
  }

  /**
   * Perform a POST request
   */
  async post<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * Perform a PUT request
   */
  async put<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  /**
   * Build query string from parameters
   */
  buildQueryString(params: Record<string, any>): string {
    const urlParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        urlParams.append(key, String(value));
      }
    });

    const queryString = urlParams.toString();
    return queryString ? `?${queryString}` : '';
  }

  /**
   * Get interaction type ID to name mapping for a project
   * Results are cached in memory for the session
   */
  async getInteractionTypeMap(project_id: number): Promise<Map<number, string>> {
    // Check cache first
    if (this.interactionTypeCache.has(project_id)) {
      return this.interactionTypeCache.get(project_id)!;
    }

    // Fetch interaction types by getting a sample of interactions
    const typeMap = new Map<number, string>();

    console.error(`[DEBUG] Fetching interaction types from /interaction-types for project ${project_id}...`);
    try {
      // Use account-level interaction-types endpoint (note: interaction types are account-wide, not project-specific)
      const types: any = await this.get(`/interaction-types?per_page=100`);
      console.error('[DEBUG] Raw interaction types response:', JSON.stringify(types, null, 2));

      let typeList: any[] = [];
      if (Array.isArray(types)) {
        typeList = types;
      } else if (types && types.data && Array.isArray(types.data)) {
        typeList = types.data;
      }

      typeList.forEach((type: any) => {
        if (type.id && type.value) {
          typeMap.set(type.id, type.value);
        } else if (type.id && type.name) {
          typeMap.set(type.id, type.name);
        }
      });
      console.error(`[DEBUG] Parsed ${typeMap.size} interaction types from main endpoint`);
      console.error('[DEBUG] Type map contents:', Array.from(typeMap.entries()));
    } catch (error) {
      console.error('[DEBUG] Main interaction types endpoint failed, using fallback:', error);
      // Fallback: fetch sample interactions and extract type info
      try {
        const response: any = await this.get(`/interactions?project_id_eq=${project_id}&per_page=50`);

        let interactions: any[] = [];
        if (Array.isArray(response)) {
          interactions = response;
        } else if (response && response.data && Array.isArray(response.data)) {
          interactions = response.data;
        }

        // Fetch details for a few interactions to get type names
        const samplesToFetch = Math.min(interactions.length, 10);
        for (let i = 0; i < samplesToFetch; i++) {
          try {
            const detailed: any = await this.get(`/interactions/${interactions[i].id}`);
            if (detailed.interaction_type && detailed.interaction_type.id) {
              const typeName = detailed.interaction_type.value || detailed.interaction_type.name || `Type ${detailed.interaction_type.id}`;
              typeMap.set(detailed.interaction_type.id, typeName);
            }
          } catch (err) {
            // Skip if we can't fetch this one
            continue;
          }

          if (typeMap.size >= 10) break;
        }
      } catch (fallbackError) {
        // If both methods fail, log and return empty map
        console.error(`Failed to fetch interaction types for project ${project_id}:`, fallbackError);
      }
    }

    // Cache the result
    this.interactionTypeCache.set(project_id, typeMap);
    return typeMap;
  }

  /**
   * Get team member ID to name mapping for a project
   * Results are cached in memory for the session
   * Note: Team members are account-level, not project-specific
   */
  async getTeamMemberMap(project_id: number): Promise<Map<number, string>> {
    // Check cache first
    if (this.teamMemberCache.has(project_id)) {
      return this.teamMemberCache.get(project_id)!;
    }

    // Fetch team members (account-level endpoint)
    const memberMap = new Map<number, string>();

    console.error(`[DEBUG] Fetching team members from /team-members for project ${project_id}...`);
    try {
      // Use account-level team-members endpoint (note: dash, not underscore)
      const members: any = await this.get(`/team-members?per_page=100`);
      console.error('[DEBUG] Raw team members response:', JSON.stringify(members, null, 2));

      let memberList: any[] = [];
      if (Array.isArray(members)) {
        memberList = members;
      } else if (members && members.data && Array.isArray(members.data)) {
        memberList = members.data;
      }

      memberList.forEach((member: any) => {
        if (member.id) {
          const name = `${member.first_name || ''} ${member.last_name || ''}`.trim() || `Team Member ${member.id}`;
          memberMap.set(member.id, name);
        }
      });
      console.error(`[DEBUG] Parsed ${memberMap.size} team members from main endpoint`);
      console.error('[DEBUG] Member map contents:', Array.from(memberMap.entries()));
    } catch (error) {
      console.error('[DEBUG] Team members endpoint failed:', error);
    }

    // Cache the result (keyed by project_id for consistency, even though data is account-wide)
    this.teamMemberCache.set(project_id, memberMap);
    return memberMap;
  }

  /**
   * Test method to check actual API response format
   * Fetches one contact to see the response structure
   */
  async testAPIResponseFormat(): Promise<void> {
    console.error('Testing Spark API response format...');
    try {
      const response = await this.get('/contacts?per_page=1');
      console.error('RAW API RESPONSE:', JSON.stringify(response, null, 2));
      console.error('Response type:', typeof response);
      console.error('Is array:', Array.isArray(response));
      if (response && typeof response === 'object') {
        console.error('Response keys:', Object.keys(response));
      }
    } catch (error) {
      console.error('API test failed:', error);
      throw error;
    }
  }
}
