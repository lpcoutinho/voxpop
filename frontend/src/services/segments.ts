import { api } from './api';
import { Segment, SegmentFilters, Supporter } from '@/types';

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface SegmentPreviewResponse {
  count: number;
  sample: Supporter[];
}

export interface CreateSegmentData {
  name: string;
  description?: string;
  filters: SegmentFilters;
}

export const segmentsService = {
  list: async (): Promise<Segment[]> => {
    const { data } = await api.get<PaginatedResponse<Segment> | Segment[]>('/supporters/segments/');
    return Array.isArray(data) ? data : data.results;
  },

  get: async (id: number): Promise<Segment> => {
    const { data } = await api.get<Segment>(`/supporters/segments/${id}/`);
    return data;
  },

  create: async (segment: CreateSegmentData): Promise<Segment> => {
    const { data } = await api.post<Segment>('/supporters/segments/', segment);
    return data;
  },

  update: async (id: number, segment: Partial<CreateSegmentData>): Promise<Segment> => {
    const { data } = await api.patch<Segment>(`/supporters/segments/${id}/`, segment);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/supporters/segments/${id}/`);
  },

  // Preview a saved segment
  preview: async (id: number): Promise<SegmentPreviewResponse> => {
    const { data } = await api.get<SegmentPreviewResponse>(`/supporters/segments/${id}/preview/`);
    return data;
  },

  // Preview filters before creating a segment
  previewFilters: async (filters: SegmentFilters): Promise<SegmentPreviewResponse> => {
    const { data } = await api.post<SegmentPreviewResponse>('/supporters/segments/preview/', { filters });
    return data;
  },

  // Duplicate a segment
  duplicate: async (id: number): Promise<Segment> => {
    const original = await segmentsService.get(id);
    return segmentsService.create({
      name: `${original.name} (Copia)`,
      description: original.description,
      filters: original.filters,
    });
  },
};
