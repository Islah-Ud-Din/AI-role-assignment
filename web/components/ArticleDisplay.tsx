'use client';

import { useState } from 'react';
import type { ArticleResponse } from '@/types/api';
import {
  FileText,
  BarChart3,
  Link2,
  ExternalLink,
  HelpCircle,
  CheckCircle2,
  XCircle,
  TrendingUp,
  Eye,
} from 'lucide-react';
import clsx from 'clsx';

interface ArticleDisplayProps {
  article: ArticleResponse;
}

export function ArticleDisplay({ article }: ArticleDisplayProps) {
  const [activeTab, setActiveTab] = useState<'content' | 'seo' | 'links' | 'faq'>('content');

  const tabs = [
    { id: 'content' as const, label: 'Content', icon: FileText },
    { id: 'seo' as const, label: 'SEO Metrics', icon: BarChart3 },
    { id: 'links' as const, label: 'Links', icon: Link2 },
    { id: 'faq' as const, label: 'FAQ', icon: HelpCircle },
  ];

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg">
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-slate-700 p-6">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
          {article.title}
        </h2>
        <div className="flex flex-wrap items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
          <span>{article.word_count.toLocaleString()} words</span>
          {article.generation_time_seconds && (
            <span>{Math.round(article.generation_time_seconds)}s generation time</span>
          )}
          {article.quality_score && (
            <span className="flex items-center gap-1">
              <TrendingUp className="w-4 h-4" />
              Quality: {article.quality_score.overall_score.toFixed(1)}/100
            </span>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 dark:border-slate-700">
        <div className="flex overflow-x-auto">
          {tabs.map((tab) => {
            const TabIcon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={clsx(
                  'flex items-center gap-2 px-6 py-4 font-medium border-b-2 transition-colors',
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600 dark:text-blue-400 dark:border-blue-400'
                    : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                )}
              >
                <TabIcon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="p-6 max-h-[600px] overflow-y-auto">
        {activeTab === 'content' && <ContentTab article={article} />}
        {activeTab === 'seo' && <SEOTab article={article} />}
        {activeTab === 'links' && <LinksTab article={article} />}
        {activeTab === 'faq' && <FAQTab article={article} />}
      </div>
    </div>
  );
}

function ContentTab({ article }: { article: ArticleResponse }) {
  return (
    <div className="prose prose-slate dark:prose-invert max-w-none">
      <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-200 mb-2">
          SEO Metadata
        </h3>
        <div className="space-y-2 text-sm">
          <div>
            <span className="font-medium">Title Tag:</span>{' '}
            <span className="text-slate-700 dark:text-slate-300">
              {article.seo_metadata.title_tag}
            </span>
          </div>
          <div>
            <span className="font-medium">Meta Description:</span>{' '}
            <span className="text-slate-700 dark:text-slate-300">
              {article.seo_metadata.meta_description}
            </span>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {article.sections.map((section, index) => {
          const HeadingTag = `h${section.level}` as keyof JSX.IntrinsicElements;
          return (
            <div key={index} className="section">
              <HeadingTag className="text-slate-900 dark:text-white font-bold mb-3">
                {section.heading}
              </HeadingTag>
              <div className="text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">
                {section.content}
              </div>
              {section.word_count > 0 && (
                <div className="text-xs text-slate-500 dark:text-slate-500 mt-2">
                  {section.word_count} words
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function SEOTab({ article }: { article: ArticleResponse }) {
  return (
    <div className="space-y-6">
      {/* Quality Score */}
      {article.quality_score && (
        <div className="p-4 bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900/20 dark:to-blue-900/20 rounded-lg border border-green-200 dark:border-green-800">
          <h3 className="font-semibold text-slate-900 dark:text-white mb-4">Quality Scores</h3>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-slate-600 dark:text-slate-400">Overall</div>
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {article.quality_score.overall_score.toFixed(1)}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-600 dark:text-slate-400">Readability</div>
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {article.quality_score.readability_score.toFixed(1)}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-600 dark:text-slate-400">SEO</div>
              <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {article.quality_score.seo_score.toFixed(1)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* SEO Validation */}
      {article.seo_validation && (
        <div className="p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg border border-slate-200 dark:border-slate-600">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-900 dark:text-white">SEO Validation</h3>
            {article.seo_validation.is_valid ? (
              <CheckCircle2 className="w-6 h-6 text-green-600 dark:text-green-400" />
            ) : (
              <XCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
            )}
          </div>
          <div className="mb-4">
            <div className="text-3xl font-bold text-slate-900 dark:text-white">
              {article.seo_validation.score.toFixed(1)}/100
            </div>
          </div>
          <div className="space-y-2">
            {Object.entries(article.seo_validation.checks).map(([check, passed]) => (
              <div key={check} className="flex items-center gap-2 text-sm">
                {passed ? (
                  <CheckCircle2 className="w-4 h-4 text-green-600 dark:text-green-400" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
                )}
                <span className="text-slate-700 dark:text-slate-300 capitalize">
                  {check.replace(/_/g, ' ')}
                </span>
              </div>
            ))}
          </div>
          {article.seo_validation.suggestions.length > 0 && (
            <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-600">
              <div className="text-sm font-medium text-slate-900 dark:text-white mb-2">
                Suggestions:
              </div>
              <ul className="list-disc list-inside space-y-1 text-sm text-slate-600 dark:text-slate-400">
                {article.seo_validation.suggestions.map((suggestion, idx) => (
                  <li key={idx}>{suggestion}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Keyword Analysis */}
      <div className="p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg border border-slate-200 dark:border-slate-600">
        <h3 className="font-semibold text-slate-900 dark:text-white mb-4">Keyword Analysis</h3>
        <div className="space-y-4">
          <div>
            <div className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Primary Keyword: {article.keyword_analysis.primary_keyword}
            </div>
            <div className="flex items-center gap-4 text-sm">
              <span className="text-slate-600 dark:text-slate-400">
                Count: {article.keyword_analysis.primary_keyword_count}
              </span>
              <span className="text-slate-600 dark:text-slate-400">
                Density: {article.keyword_analysis.primary_keyword_density.toFixed(2)}%
              </span>
            </div>
          </div>
          {Object.keys(article.keyword_analysis.secondary_keywords).length > 0 && (
            <div>
              <div className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Secondary Keywords:
              </div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(article.keyword_analysis.secondary_keywords).map(
                  ([keyword, count]) => (
                    <span
                      key={keyword}
                      className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 rounded text-xs"
                    >
                      {keyword} ({count})
                    </span>
                  )
                )}
              </div>
            </div>
          )}
          {article.keyword_analysis.lsi_keywords.length > 0 && (
            <div>
              <div className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                LSI Keywords:
              </div>
              <div className="flex flex-wrap gap-2">
                {article.keyword_analysis.lsi_keywords.map((keyword) => (
                  <span
                    key={keyword}
                    className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200 rounded text-xs"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function LinksTab({ article }: { article: ArticleResponse }) {
  return (
    <div className="space-y-6">
      {/* Internal Links */}
      {article.internal_links.length > 0 && (
        <div>
          <h3 className="font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
            <Link2 className="w-5 h-5" />
            Internal Links ({article.internal_links.length})
          </h3>
          <div className="space-y-3">
            {article.internal_links.map((link, idx) => (
              <div
                key={idx}
                className="p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg border border-slate-200 dark:border-slate-600"
              >
                <div className="font-medium text-slate-900 dark:text-white mb-1">
                  {link.anchor_text}
                </div>
                <div className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                  Target: {link.suggested_target_topic}
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-500 mb-2">
                  {link.context}
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-xs text-slate-600 dark:text-slate-400">
                    Relevance: {(link.relevance_score * 100).toFixed(0)}%
                  </div>
                  <div className="flex-1 h-2 bg-slate-200 dark:bg-slate-600 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500"
                      style={{ width: `${link.relevance_score * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* External References */}
      {article.external_references.length > 0 && (
        <div>
          <h3 className="font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
            <ExternalLink className="w-5 h-5" />
            External References ({article.external_references.length})
          </h3>
          <div className="space-y-3">
            {article.external_references.map((ref, idx) => (
              <div
                key={idx}
                className="p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg border border-slate-200 dark:border-slate-600"
              >
                <div className="font-medium text-slate-900 dark:text-white mb-1">
                  {ref.source_name}
                </div>
                <div className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                  Type: {ref.source_type}
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-500 mb-2">
                  {ref.citation_context}
                </div>
                <div className="text-xs text-slate-600 dark:text-slate-400 italic">
                  {ref.credibility_reason}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function FAQTab({ article }: { article: ArticleResponse }) {
  if (article.faq_section.length === 0) {
    return (
      <div className="text-center py-12 text-slate-500 dark:text-slate-400">
        <HelpCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>No FAQ section available</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {article.faq_section.map((faq, idx) => (
        <div
          key={idx}
          className="p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg border border-slate-200 dark:border-slate-600"
        >
          <div className="font-semibold text-slate-900 dark:text-white mb-2 flex items-start gap-2">
            <HelpCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
            {faq.question}
          </div>
          <div className="text-slate-700 dark:text-slate-300 ml-7">{faq.answer}</div>
        </div>
      ))}
    </div>
  );
}
