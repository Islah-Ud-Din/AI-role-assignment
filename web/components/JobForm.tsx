'use client';

import { useState } from 'react';
import type { ArticleRequest } from '@/types/api';
import { Sparkles, Loader2 } from 'lucide-react';

interface JobFormProps {
  onSubmit: (request: ArticleRequest) => void;
  loading?: boolean;
}

export function JobForm({ onSubmit, loading = false }: JobFormProps) {
  const [topic, setTopic] = useState('');
  const [wordCount, setWordCount] = useState(1500);
  const [language, setLanguage] = useState('en');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;

    onSubmit({
      topic: topic.trim(),
      target_word_count: wordCount,
      language,
    });

    // Reset form
    setTopic('');
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="topic" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
          Topic / Keyword *
        </label>
        <input
          id="topic"
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g., best productivity tools for remote teams"
          className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          required
          disabled={loading}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="wordCount" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Word Count
          </label>
          <input
            id="wordCount"
            type="number"
            value={wordCount}
            onChange={(e) => setWordCount(parseInt(e.target.value) || 1500)}
            min={500}
            max={10000}
            step={100}
            className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
        </div>

        <div>
          <label htmlFor="language" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Language
          </label>
          <select
            id="language"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          >
            <option value="en">English</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="de">German</option>
            <option value="it">Italian</option>
          </select>
        </div>
      </div>

      <button
        type="submit"
        disabled={loading || !topic.trim()}
        className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
      >
        {loading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Creating...
          </>
        ) : (
          <>
            <Sparkles className="w-5 h-5" />
            Generate Article
          </>
        )}
      </button>
    </form>
  );
}
