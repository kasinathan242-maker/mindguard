import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch } from '@/lib/api';
import type { Locale } from '@/lib/i18n';

export type InstrumentType = 'PHQ9' | 'GAD7';
export type NextStep = 'self_care' | 'talk_to_someone' | 'consult_professional';

export const INSTRUMENT_TYPES: InstrumentType[] = ['PHQ9', 'GAD7'];

/** 0-based index of the PHQ-9 item about thoughts of death or self-harm. */
export const PHQ9_SAFETY_ITEM = 8;

export interface Option {
  value: number;
  label: string;
}

export interface Instrument {
  type: InstrumentType;
  title: string;
  stem: string;
  items: { index: number; text: string }[];
  options: Option[];
  difficulty_question: string;
  difficulty_options: Option[];
  item_locale: 'en';
  requested_locale: Locale;
  translation_available: boolean;
  attribution: string;
}

export interface AssessmentResult {
  id: string;
  type: InstrumentType;
  total: number;
  max_score: number;
  severity_band: string;
  next_step: NextStep;
  safety_item_positive: boolean;
  functional_difficulty: number | null;
  created_at: string;
}

const HISTORY_KEY = ['assessments', 'history'] as const;

export function useInstrument(type: InstrumentType, locale: Locale) {
  return useQuery({
    queryKey: ['assessments', 'instrument', type, locale],
    queryFn: ({ signal }) =>
      apiFetch<Instrument>(`/assessments/${type}/items?locale=${locale}`, { signal }),
    staleTime: Infinity,
  });
}

export function useAssessmentHistory() {
  return useQuery({
    queryKey: HISTORY_KEY,
    queryFn: ({ signal }) => apiFetch<AssessmentResult[]>('/assessments/history', { signal }),
  });
}

export function useSubmitAssessment(type: InstrumentType) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: { answers: number[]; functional_difficulty: number | null }) =>
      apiFetch<AssessmentResult>(`/assessments/${type}`, { method: 'POST', body: input }),
    onSuccess: () => client.invalidateQueries({ queryKey: HISTORY_KEY }),
  });
}
