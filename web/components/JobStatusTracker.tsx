'use client';

import { formatDistanceToNow } from 'date-fns';
import type { JobResponse, JobStatus } from '@/types/api';
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  Loader2,
  Search,
  FileText,
  PenTool,
  ShieldCheck,
} from 'lucide-react';
import clsx from 'clsx';

interface JobStatusTrackerProps {
  job: JobResponse;
}

const statusSteps: { status: JobStatus; label: string; icon: any }[] = [
  { status: 'pending', label: 'Pending', icon: Clock },
  { status: 'researching', label: 'Researching', icon: Search },
  { status: 'analyzing', label: 'Analyzing', icon: Search },
  { status: 'outlining', label: 'Outlining', icon: FileText },
  { status: 'generating', label: 'Generating', icon: PenTool },
  { status: 'validating', label: 'Validating', icon: ShieldCheck },
  { status: 'completed', label: 'Completed', icon: CheckCircle2 },
];

export function JobStatusTracker({ job }: JobStatusTrackerProps) {
  const currentStepIndex = statusSteps.findIndex((step) => step.status === job.status);
  const isCompleted = job.status === 'completed';
  const isFailed = job.status === 'failed';

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
            Job Status
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            {job.topic || 'Untitled'}
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {Math.round(job.progress)}%
          </div>
          <div className="text-xs text-slate-500 dark:text-slate-500">
            {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="w-full h-3 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
          <div
            className={clsx(
              'h-full transition-all duration-500',
              isFailed
                ? 'bg-red-500'
                : isCompleted
                ? 'bg-green-500'
                : 'bg-blue-500'
            )}
            style={{ width: `${job.progress}%` }}
          />
        </div>
      </div>

      {/* Status Steps */}
      <div className="space-y-4">
        {statusSteps.map((step, index) => {
          const StepIcon = step.icon;
          const isActive = index === currentStepIndex;
          const isPast = index < currentStepIndex || isCompleted;
          const isCurrent = isActive && !isCompleted && !isFailed;

          return (
            <div
              key={step.status}
              className={clsx(
                'flex items-center gap-4 p-3 rounded-lg transition-colors',
                isCurrent && 'bg-blue-50 dark:bg-blue-900/20',
                isPast && !isCurrent && 'bg-green-50 dark:bg-green-900/20',
                isFailed && index === currentStepIndex && 'bg-red-50 dark:bg-red-900/20'
              )}
            >
              <div
                className={clsx(
                  'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center',
                  isPast && !isCurrent
                    ? 'bg-green-500 text-white'
                    : isCurrent
                    ? 'bg-blue-500 text-white'
                    : isFailed && index === currentStepIndex
                    ? 'bg-red-500 text-white'
                    : 'bg-slate-200 dark:bg-slate-700 text-slate-500 dark:text-slate-400'
                )}
              >
                {isCurrent && !isFailed ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <StepIcon className="w-5 h-5" />
                )}
              </div>
              <div className="flex-1">
                <div className="font-medium text-slate-900 dark:text-white">
                  {step.label}
                </div>
                {isActive && job.current_step && (
                  <div className="text-sm text-slate-600 dark:text-slate-400">
                    {job.current_step}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Error Message */}
      {isFailed && job.error_message && (
        <div className="mt-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-medium text-red-900 dark:text-red-200">Job Failed</div>
              <div className="text-sm text-red-800 dark:text-red-300 mt-1">
                {job.error_message}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Job Metadata */}
      <div className="mt-6 pt-6 border-t border-slate-200 dark:border-slate-700 grid grid-cols-2 gap-4 text-sm">
        <div>
          <div className="text-slate-500 dark:text-slate-400">Job ID</div>
          <div className="font-mono text-xs text-slate-900 dark:text-white break-all">
            {job.job_id}
          </div>
        </div>
        <div>
          <div className="text-slate-500 dark:text-slate-400">Status</div>
          <div className="font-medium text-slate-900 dark:text-white capitalize">
            {job.status}
          </div>
        </div>
        {job.completed_at && (
          <div>
            <div className="text-slate-500 dark:text-slate-400">Completed</div>
            <div className="text-slate-900 dark:text-white">
              {formatDistanceToNow(new Date(job.completed_at), { addSuffix: true })}
            </div>
          </div>
        )}
        <div>
          <div className="text-slate-500 dark:text-slate-400">Checkpoints</div>
          <div className="text-slate-900 dark:text-white">
            {job.serp_data_collected && '✓ SERP'} {job.outline_generated && '✓ Outline'}
          </div>
        </div>
      </div>
    </div>
  );
}
