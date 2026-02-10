'use client';

import { formatDistanceToNow } from 'date-fns';
import type { JobResponse, JobStatus } from '@/types/api';
import { CheckCircle2, Clock, AlertCircle, PlayCircle, Loader2 } from 'lucide-react';
import clsx from 'clsx';

interface JobListProps {
  jobs: JobResponse[];
  currentJobId?: string;
  onSelectJob: (jobId: string) => void;
  onResumeJob: (jobId: string) => void;
  loading?: boolean;
}

const statusConfig: Record<JobStatus, { icon: any; color: string; label: string }> = {
  pending: { icon: Clock, color: 'text-yellow-600 dark:text-yellow-400', label: 'Pending' },
  researching: { icon: Loader2, color: 'text-blue-600 dark:text-blue-400', label: 'Researching' },
  analyzing: { icon: Loader2, color: 'text-blue-600 dark:text-blue-400', label: 'Analyzing' },
  outlining: { icon: Loader2, color: 'text-purple-600 dark:text-purple-400', label: 'Outlining' },
  generating: { icon: Loader2, color: 'text-indigo-600 dark:text-indigo-400', label: 'Generating' },
  validating: { icon: Loader2, color: 'text-green-600 dark:text-green-400', label: 'Validating' },
  completed: { icon: CheckCircle2, color: 'text-green-600 dark:text-green-400', label: 'Completed' },
  failed: { icon: AlertCircle, color: 'text-red-600 dark:text-red-400', label: 'Failed' },
};

export function JobList({ jobs, currentJobId, onSelectJob, onResumeJob, loading }: JobListProps) {
  if (loading && jobs.length === 0) {
    return (
      <div className="text-center py-8">
        <Loader2 className="w-6 h-6 mx-auto animate-spin text-slate-400" />
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500 dark:text-slate-400">
        <p>No jobs yet. Create your first article!</p>
      </div>
    );
  }

  return (
    <div className="space-y-2 max-h-96 overflow-y-auto">
      {jobs.map((job) => {
        const StatusIcon = statusConfig[job.status].icon;
        const isActive = job.job_id === currentJobId;
        const isActiveStatus = ['researching', 'analyzing', 'outlining', 'generating', 'validating'].includes(job.status);

        return (
          <div
            key={job.job_id}
            className={clsx(
              'p-4 rounded-lg border cursor-pointer transition-all',
              isActive
                ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700'
                : 'bg-slate-50 dark:bg-slate-700/50 border-slate-200 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700'
            )}
            onClick={() => onSelectJob(job.job_id)}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <StatusIcon
                    className={clsx(
                      'w-4 h-4 flex-shrink-0',
                      statusConfig[job.status].color,
                      isActiveStatus && 'animate-spin'
                    )}
                  />
                  <span className="text-sm font-medium text-slate-900 dark:text-white truncate">
                    {job.status === 'completed' && job.result ? job.result.title : job.topic || 'Untitled'}
                  </span>
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400 truncate">
                  {job.current_step || statusConfig[job.status].label}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">
                  {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}
                </p>
              </div>
              <div className="flex flex-col items-end gap-1">
                {job.status === 'failed' && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onResumeJob(job.job_id);
                    }}
                    className="p-1 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded"
                    title="Resume job"
                  >
                    <PlayCircle className="w-4 h-4" />
                  </button>
                )}
                {job.progress > 0 && (
                  <div className="w-12 h-1 bg-slate-200 dark:bg-slate-600 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-600 dark:bg-blue-400 transition-all"
                      style={{ width: `${job.progress}%` }}
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
