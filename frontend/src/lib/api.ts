import { Signal, Entity, TimelineEvent } from './data';

const DEFAULT_PROD_URL = 'https://signal-ai-executive.onrender.com';
const BASE_URL = import.meta.env.VITE_API_BASE_URL
  ? import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '')
  : (typeof window !== 'undefined' && window.location.hostname.includes('vercel.app') ? DEFAULT_PROD_URL : '');
const API_BASE_URL = `${BASE_URL}/api/v1`;

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('signal_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeader(),
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    localStorage.removeItem('signal_token');
    window.dispatchEvent(new Event('signal-unauthorized'));
    throw new Error('Unauthorized');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `API request failed with status ${response.status}`);
  }

  return response.json();
}

// Transform raw backend signal object to frontend Signal interface
export function transformBackendSignal(raw: any): Signal {
  const detectedAction = raw.detected_actions?.[0]?.action || 'no-action';
  const actionTypeMap: Record<string, Signal['actionType']> = {
    reply: 'reply',
    pay: 'pay',
    upload: 'upload',
    complete: 'complete',
    review: 'review',
  };

  const detectedDeadline = raw.detected_deadlines?.[0];
  const deadlineText = detectedDeadline?.description || (detectedDeadline?.date ? `Due ${new Date(detectedDeadline.date).toLocaleDateString()}` : undefined);

  return {
    id: raw.id,
    subject: raw.subject || '(No Subject)',
    sender: raw.sender_name || raw.sender_email?.split('@')[0] || 'Unknown',
    senderEmail: raw.sender_email || '',
    preview: raw.summary || raw.snippet || '(No preview content)',
    category: raw.extracted_metadata?.category || 'personal',
    bucket: (raw.bucket || 'today') as Signal['bucket'],
    status: raw.is_read ? 'stable' : 'new',
    priority: raw.priority_score || 50,
    actionType: actionTypeMap[detectedAction] || 'no-action',
    deadline: detectedDeadline?.date,
    deadlineText,
    entityName: raw.extracted_metadata?.company || raw.extracted_metadata?.entity_name || raw.sender_name || 'General Item',
    entityType: raw.extracted_metadata?.entity_type || 'general',
    gmailUrl: raw.gmail_link || `https://mail.google.com/mail/u/0/#inbox/${raw.gmail_message_id || ''}`,
    createdAt: raw.received_at || new Date().toISOString(),
    updatedAt: raw.received_at || new Date().toISOString(),
  };
}

// Transform raw backend entity object to frontend Entity interface
export function transformBackendEntity(raw: any): Entity {
  return {
    id: raw.id,
    name: raw.name,
    type: raw.entity_type || 'general',
    category: raw.metadata?.category || 'general',
    lastUpdated: raw.last_updated_at || new Date().toISOString(),
    events: (raw.events || []).map((e: any): TimelineEvent => ({
      id: e.id,
      timestamp: e.event_date || new Date().toISOString(),
      subject: e.title,
      summary: e.description || '',
    })),
  };
}

export const api = {
  // Auth
  getGoogleAuthUrl: async (): Promise<string> => {
    const data = await request<{ auth_url: string }>('/auth/google/login');
    return data.auth_url;
  },

  getMe: async (): Promise<any> => {
    return request<any>('/auth/me');
  },

  // Overview
  getOverview: async (): Promise<any> => {
    const data = await request<any>('/overview');
    return {
      ...data,
      needs_action: (data.needs_action || []).map(transformBackendSignal),
      changed: (data.changed || []).map(transformBackendSignal),
      due_soon: (data.due_soon || []).map(transformBackendSignal),
    };
  },

  // Focus / Buckets
  getFocusSummary: async (): Promise<any> => {
    return request<any>('/focus');
  },

  getSignalsByBucket: async (bucket: string): Promise<Signal[]> => {
    const data = await request<any[]>(`/focus/${bucket}`);
    return data.map(transformBackendSignal);
  },

  moveSignalBucket: async (signalId: string, newBucket: string, reason?: string): Promise<Signal> => {
    const data = await request<any>(`/focus/${signalId}/move`, {
      method: 'PATCH',
      body: JSON.stringify({ new_bucket: newBucket, reason }),
    });
    return transformBackendSignal(data);
  },

  // Signals CRUD & Sync
  getSignals: async (limit = 50, offset = 0, bucket?: string): Promise<Signal[]> => {
    let query = `?limit=${limit}&offset=${offset}`;
    if (bucket) query += `&bucket=${bucket}`;
    const data = await request<any[]>(`/signals${query}`);
    return data.map(transformBackendSignal);
  },

  archiveSignal: async (signalId: string): Promise<Signal> => {
    const data = await request<any>(`/signals/${signalId}/archive`, {
      method: 'POST',
    });
    return transformBackendSignal(data);
  },

  triggerSync: async (): Promise<{ message: string }> => {
    return request<{ message: string }>('/signals/sync', {
      method: 'POST',
    });
  },

  // Timeline
  getTimeline: async (): Promise<Entity[]> => {
    const data = await request<any[]>('/timeline');
    return data.map(transformBackendEntity);
  },

  // Behavior Insights
  getBehavior: async (): Promise<any> => {
    return request<any>('/behavior');
  },

  // Ask Signal (AI Chat)
  askSignal: async (query: string): Promise<any> => {
    return request<any>('/ask', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  },
};
