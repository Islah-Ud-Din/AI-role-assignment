// Type definitions matching the FastAPI backend schemas

export enum JobStatus {
  PENDING = "pending",
  RESEARCHING = "researching",
  ANALYZING = "analyzing",
  OUTLINING = "outlining",
  GENERATING = "generating",
  VALIDATING = "validating",
  COMPLETED = "completed",
  FAILED = "failed",
}

export interface ArticleRequest {
  topic: string;
  target_word_count?: number;
  language?: string;
}

export interface ArticleSection {
  heading: string;
  level: number;
  content: string;
  word_count: number;
}

export interface KeywordAnalysis {
  primary_keyword: string;
  primary_keyword_count: number;
  primary_keyword_density: number;
  secondary_keywords: Record<string, number>;
  lsi_keywords: string[];
}

export interface LinkSuggestion {
  anchor_text: string;
  suggested_target_topic: string;
  context: string;
  relevance_score: number;
}

export interface ExternalReference {
  source_name: string;
  source_type: string;
  url?: string | null;
  citation_context: string;
  credibility_reason: string;
}

export interface SEOMetadata {
  title_tag: string;
  meta_description: string;
  og_title?: string | null;
  og_description?: string | null;
  canonical_url_suggestion?: string | null;
  focus_keyword: string;
  secondary_keywords: string[];
}

export interface FAQItem {
  question: string;
  answer: string;
}

export interface SEOValidationResult {
  is_valid: boolean;
  score: number;
  checks: Record<string, boolean>;
  issues: string[];
  suggestions: string[];
}

export interface QualityScore {
  overall_score: number;
  readability_score: number;
  seo_score: number;
  uniqueness_indicators: Record<string, number>;
  improvement_suggestions: string[];
  needs_revision: boolean;
}

export interface ArticleResponse {
  title: string;
  sections: ArticleSection[];
  full_content: string;
  word_count: number;
  seo_metadata: SEOMetadata;
  keyword_analysis: KeywordAnalysis;
  internal_links: LinkSuggestion[];
  external_references: ExternalReference[];
  faq_section: FAQItem[];
  quality_score?: QualityScore | null;
  seo_validation?: SEOValidationResult | null;
  generation_time_seconds: number;
  serp_analysis_summary?: Record<string, any> | null;
}

export interface JobResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  current_step?: string | null;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
  error_message?: string | null;
  result?: ArticleResponse | null;
  serp_data_collected: boolean;
  outline_generated: boolean;
}

export interface JobCreateResponse {
  job_id: string;
  status: JobStatus;
  message: string;
}

export interface SERPResult {
  rank: number;
  url: string;
  title: string;
  snippet: string;
  domain?: string | null;
}

export interface ThemeAnalysis {
  theme: string;
  frequency: number;
  related_keywords: string[];
  example_headings: string[];
}

export interface SERPAnalysis {
  query: string;
  total_results: number;
  results: SERPResult[];
  common_themes: ThemeAnalysis[];
  common_questions: string[];
  avg_title_length: number;
  avg_content_indicators: Record<string, number>;
  top_domains: string[];
}

export interface OutlineSection {
  heading: string;
  level: number;
  key_points: string[];
  target_word_count: number;
  keywords_to_include: string[];
}

export interface ArticleOutline {
  title: string;
  meta_description: string;
  primary_keyword: string;
  secondary_keywords: string[];
  sections: OutlineSection[];
  estimated_word_count: number;
  target_audience: string;
  content_angle: string;
}
