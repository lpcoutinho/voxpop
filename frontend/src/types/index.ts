// Auth Types
export interface User {
  id: number;
  email: string;
  name: string;
  first_name?: string;
  last_name?: string;
  avatar?: string;
  role: 'admin' | 'manager' | 'operator';
  is_superuser?: boolean;
  is_staff?: boolean;
  is_verified?: boolean;
  is_active?: boolean;
  force_password_change?: boolean;
  last_login?: string;
  date_joined?: string;
}

export interface Tenant {
  id: number;
  name: string;
  slug: string;
  logo?: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

// Supporter Types
export interface Tag {
  id: number;
  name: string;
  slug?: string;
  color: string;
  description?: string;
  is_system?: boolean;
  is_active?: boolean;
  supporters_count?: number;
  leads_count?: number;
  apoiadores_count?: number;
  created_at: string;
}

export type ContactStatus = 'lead' | 'apoiador' | 'blacklist';

export interface Supporter {
  id: number;
  name: string;
  phone: string;
  email?: string;
  cpf?: string;
  city?: string;
  state?: string;
  neighborhood?: string;
  zip_code?: string;
  electoral_zone?: string;
  electoral_section?: string;
  birth_date?: string;
  gender?: 'M' | 'F' | 'O';
  tags: Tag[];
  whatsapp_opt_in: boolean;
  opt_in_date?: string;
  source: 'import' | 'form' | 'manual' | 'api';
  extra_data?: Record<string, unknown>;
  // Status fields (computed from tags)
  is_lead: boolean;
  is_supporter_status: boolean;
  is_blacklisted: boolean;
  contact_status: ContactStatus;
  age?: number;
  can_receive_messages?: boolean;
  created_at: string;
  updated_at: string;
}

// Segment Types
export interface SegmentFilters {
  contact_status?: 'lead' | 'apoiador' | 'blacklist';
  city?: string;
  state?: string;
  neighborhood?: string;
  gender?: string;
  tags?: number[];
  tags_all?: number[];
  age_min?: number;
  age_max?: number;
  electoral_zone?: string;
  electoral_section?: string;
  source?: string;
}

export interface Segment {
  id: number;
  name: string;
  description?: string;
  filters: SegmentFilters;
  cached_count: number;
  leads_count?: number;
  supporters_count?: number;
  is_active: boolean;
  created_by?: number;
  created_by_name?: string;
  created_at: string;
  updated_at: string;
}

// Template Types
export interface MessageTemplate {
  id: number;
  name: string;
  type?: 'text' | 'image' | 'document' | 'audio' | 'video';
  message_type?: 'text' | 'image' | 'document' | 'audio' | 'video';
  content?: string;
  message?: string;
  media_url?: string;
  created_at: string;
  updated_at: string;
}

// WhatsApp Types
export type WhatsAppSessionStatus = 'connected' | 'connecting' | 'disconnected' | 'banned';

export interface WhatsAppSession {
  id: number;
  name: string;
  phone_number?: string;
  status: WhatsAppSessionStatus;
  status_display?: string;
  messages_sent_today: number;
  daily_message_limit: number;
  remaining_messages?: number;
  is_active: boolean;
  is_healthy: boolean;
  created_at: string;
  access_token?: string;
}

// Campaign Types
export type CampaignStatus = 'draft' | 'scheduled' | 'running' | 'paused' | 'completed' | 'cancelled';

export interface Campaign {
  id: number;
  name: string;
  description?: string;
  status: CampaignStatus;
  segment_id?: number;
  template_id?: number;
  whatsapp_session_id: number;
  scheduled_at?: string;
  messages_per_minute: number;
  total_recipients: number;
  messages_sent: number;
  messages_delivered: number;
  messages_read: number;
  messages_failed: number;
  media_url?: string;
  media_type?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

// Dashboard Types
export interface DashboardOverview {
  total_supporters: number;
  messages_sent_month: number;
  delivery_rate: number;
  read_rate: number;
  active_campaigns: number;
  whatsapp_sessions: {
    connected: number;
    total: number;
  };
}

export interface DashboardMetrics {
  date: string;
  messages_sent: number;
  messages_delivered: number;
  messages_read: number;
  messages_failed: number;
}

// API Response Types
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Admin Types
export interface Plan {
  id: number;
  name: string;
  slug: string;
  description?: string;
  max_supporters: number;
  max_messages_month: number;
  max_campaigns: number;
  max_whatsapp_sessions: number;
  price: number;
  is_active: boolean;
  is_public: boolean;
  tenants_count?: number;
  created_at: string;
  updated_at: string;
}

export interface Organization {
  id: number;
  name: string;
  slug: string;
  schema_name: string;
  document?: string;
  email?: string;
  phone?: string;
  plan?: Plan;
  plan_id?: number;
  is_active: boolean;
  settings?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  // Stats
  supporters_count?: number;
  campaigns_count?: number;
  messages_sent?: number;
  owner?: {
    id: number;
    email: string;
    name: string;
  };
}

export interface AdminStats {
  total_organizations: number;
  active_organizations: number;
  total_users: number;
  total_supporters: number;
  total_campaigns: number;
  total_messages: number;
  messages_this_month: number;
  recent_organizations: Organization[];
}

export interface AdminUser extends User {
  organizations?: Array<{
    id: number;
    name: string;
    role: string;
  }>;
}
