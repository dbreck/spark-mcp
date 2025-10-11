/**
 * TypeScript interfaces for Spark.re API responses
 */

export interface Contact {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  address?: string;
  city?: string;
  postcode?: string;
  country_name?: string;
  country_iso?: string;
  agent?: boolean;
  brokerage_id?: number;
  contact_group_id?: number;
  project_id?: number;
  project_name?: string;
  rating_id?: number;
  rating?: string;
  marketing_source?: string;
  team_member_id?: number;
  registered_at?: string;
  created_at: string;
  updated_at: string;
  last_interaction_date?: string;
  notes?: string;
  recent_interactions?: Interaction[];
  projects?: ProjectReference[];
}

export interface ContactListResponse {
  data: Contact[];
  meta: PaginationMeta;
}

export interface Project {
  id: number;
  name: string;
  kind?: string;
  sales_stage?: string;
  country_name?: string;
  country_iso?: string;
  province?: string;
  state?: string;
  lease?: boolean;
  start_date?: string;
  created_at: string;
  updated_at: string;
  total_contacts?: number;
  conversions?: number;
  hot_leads?: number;
  warm_leads?: number;
}

export interface ProjectListResponse {
  data: Project[];
  meta: PaginationMeta;
}

export interface ProjectReference {
  id: number;
  name: string;
  status?: string;
}

export interface Interaction {
  id: number;
  contact_id: number;
  interaction_type_id?: number;
  interaction_type?: string;
  team_member_id?: number;
  creator_id?: number;
  timestamp?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface InteractionListResponse {
  data: Interaction[];
  meta: PaginationMeta;
}

export interface PaginationMeta {
  current_page: number;
  per_page: number;
  total_pages: number;
  total_count: number;
}

export interface PaginationInfo {
  currentPage: number;
  firstPage?: number;
  lastPage?: number;
  nextPage?: number;
  prevPage?: number;
  hasMore: boolean;
  totalPages?: number;
}

export interface PaginatedResponse<T> {
  data: T;
  pagination: PaginationInfo;
}

export interface ProjectAnalytics {
  project_id: number;
  project_name: string;
  date_range: string;
  total_contacts: number;
  new_contacts: number;
  conversions: number;
  conversion_rate: number;
  hot_leads: number;
  warm_leads: number;
  cold_leads: number;
  sources?: LeadSource[];
  registration_trend?: RegistrationTrendPoint[];
}

export interface LeadSource {
  name: string;
  count: number;
  percentage: number;
}

export interface RegistrationTrendPoint {
  date: string;
  count: number;
}

export interface APIError {
  message: string;
  status?: number;
  errors?: Record<string, string[]>;
}
