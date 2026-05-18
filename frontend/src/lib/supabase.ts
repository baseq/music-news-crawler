import { createClient } from "@supabase/supabase-js";

const url  = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(url, anon);

// ── Types matching DB schema ────────────────────────────────────

export interface Channel {
  id:              string;
  slug:            string;
  name:            string;
  description:     string;
  icon:            string;
  genre_filters:   string[] | null;
  content_filters: string[] | null;
  sort_order:      number;
}

export interface Article {
  id:           string;
  url:          string;
  title:        string;
  author:       string | null;
  image_url:    string | null;
  published_at: string | null;
  summary_en:   string | null;
  genres:       string[];
  content_type: string | null;
  sentiment:    string | null;
  sources:      { name: string; language: string } | null;
}

export interface ArticleWithTranslation extends Article {
  display_summary: string;   // summary in chosen language
}
