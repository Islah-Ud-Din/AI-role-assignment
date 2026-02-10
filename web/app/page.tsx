'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import type { JobResponse, ArticleRequest } from '@/types/api';
import { JobForm } from '@/components/JobForm';
import { JobList } from '@/components/JobList';
import { JobStatusTracker } from '@/components/JobStatusTracker';
import { ArticleDisplay } from '@/components/ArticleDisplay';
import { FileText, Loader2 } from 'lucide-react';

export default function Home() {
  const [currentJob, setCurrentJob] = useState<JobResponse | null>(null);
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load jobs on mount
  useEffect(() => {
    loadJobs();
  }, []);

  // Poll for job updates if there's an active job
  useEffect(() => {
    if (!currentJob || currentJob.status === 'completed' || currentJob.status === 'failed') {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const updatedJob = await apiClient.getJob(currentJob.job_id);
        setCurrentJob(updatedJob);
        
        if (updatedJob.status === 'completed' || updatedJob.status === 'failed') {
          loadJobs(); // Refresh job list
        }
      } catch (err) {
        console.error('Failed to poll job status:', err);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [currentJob]);

  const loadJobs = async () => {
    try {
      setLoading(true);
      const jobList = await apiClient.listJobs();
      setJobs(jobList);
    } catch (err: any) {
      setError(err.message || 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateJob = async (request: ArticleRequest) => {
    try {
      setError(null);
      setLoading(true);
      const response = await apiClient.createJob(request);
      const job = await apiClient.getJob(response.job_id);
      setCurrentJob(job);
      await loadJobs();
    } catch (err: any) {
      setError(err.message || 'Failed to create job');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectJob = async (jobId: string) => {
    try {
      const job = await apiClient.getJob(jobId);
      setCurrentJob(job);
    } catch (err: any) {
      setError(err.message || 'Failed to load job');
    }
  };

  const handleResumeJob = async (jobId: string) => {
    try {
      setError(null);
      await apiClient.resumeJob(jobId);
      const job = await apiClient.getJob(jobId);
      setCurrentJob(job);
      await loadJobs();
    } catch (err: any) {
      setError(err.message || 'Failed to resume job');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-3">
            <FileText className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            <div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                SEO Article Generator
              </h1>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                AI-powered content generation platform
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Form and Job List */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-slate-900 dark:text-white">
                Create New Article
              </h2>
              <JobForm onSubmit={handleCreateJob} loading={loading} />
            </div>

            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-semibold mb-4 text-slate-900 dark:text-white">
                Recent Jobs
              </h2>
              <JobList
                jobs={jobs}
                currentJobId={currentJob?.job_id}
                onSelectJob={handleSelectJob}
                onResumeJob={handleResumeJob}
                loading={loading}
              />
            </div>
          </div>

          {/* Right Column - Job Status and Article */}
          <div className="lg:col-span-2 space-y-6">
            {currentJob ? (
              <>
                <JobStatusTracker job={currentJob} />
                {currentJob.result && (
                  <ArticleDisplay article={currentJob.result} />
                )}
              </>
            ) : (
              <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-12 text-center">
                <Loader2 className="w-16 h-16 mx-auto text-slate-400 mb-4 animate-spin" />
                <p className="text-slate-600 dark:text-slate-400">
                  Select a job or create a new article to get started
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
