'use client';

import React, { useState } from 'react';
import { Loader2, CheckCircle, XCircle, Clock } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { useFixJobStatus } from '@/hooks/useCompliance';
import { FixResultModal } from './FixResultModal';

interface ActiveJobsPanelProps {
  jobs: any[];
}

export const ActiveJobsPanel: React.FC<ActiveJobsPanelProps> = ({ jobs }) => {
  if (!jobs || jobs.length === 0) {
    return null;
  }

  // Separate jobs by status
  const processingJobs = jobs.filter(j => ['pending', 'processing'].includes(j.status));
  const completedJobs = jobs.filter(j => j.status === 'completed');
  const failedJobs = jobs.filter(j => j.status === 'failed');

  return (
    <Card className="bg-gradient-to-br from-blue-50 to-purple-50 border-blue-200">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          {processingJobs.length > 0 ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
              🤖 KI-Fixes werden generiert...
            </>
          ) : (
            <>
              <CheckCircle className="w-5 h-5 text-green-600" />
              ✅ KI-Fixes
            </>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {jobs.map((job) => (
            <JobStatusCard key={job.job_id} job={job} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

const JobStatusCard: React.FC<{ job: any }> = ({ job }) => {
  // Polling für Job-Status
  const { data: jobStatus } = useFixJobStatus(job.job_id);
  const [showResultModal, setShowResultModal] = useState(false);
  
  const status = jobStatus?.status || job.status || 'processing';
  const progress = jobStatus?.progress_percent || job.progress_percent || (status === 'pending' ? 10 : 0);
  const currentStep = jobStatus?.current_step || job.current_step || (status === 'pending' ? 'KI analysiert Problem...' : 'Initialisierung...');
  
  // Parse result if it's a string
  let parsedResult = jobStatus?.result;
  if (typeof parsedResult === 'string') {
    try {
      parsedResult = JSON.parse(parsedResult);
    } catch (e) {
      console.error('Failed to parse fix result:', e);
    }
  }

  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'processing':
      case 'pending':
        return <Loader2 className="w-5 h-5 animate-spin text-blue-600" />;
      default:
        return <Loader2 className="w-5 h-5 animate-spin text-blue-600" />;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'completed':
        return 'Abgeschlossen!';
      case 'failed':
        return 'Fehler aufgetreten';
      case 'processing':
        return 'Wird generiert...';
      case 'pending':
        return 'Wird generiert...';
      default:
        return 'Wird generiert...';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      case 'processing':
      case 'pending':
        return 'bg-blue-500';
      default:
        return 'bg-blue-500';
    }
  };

  return (
    <div className="p-4 bg-white rounded-lg border border-blue-200 shadow-sm">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          {getStatusIcon()}
          <div>
            <p className="font-semibold text-gray-900">
              {job.issue_title || job.issue_id.slice(0, 8)}
            </p>
            <p className="text-sm text-gray-600">{getStatusText()}</p>
          </div>
        </div>
        <span className="text-sm font-medium text-blue-600">
          {progress}%
        </span>
      </div>

      {/* Progress Bar */}
      <div className="mb-2">
        <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full ${getStatusColor()} transition-all duration-500`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Current Step */}
      <p className="text-sm text-gray-600">
        {currentStep}
      </p>

      {/* Estimated Time (nur wenn processing) */}
      {status === 'processing' && job.estimated_completion && (
        <p className="text-xs text-gray-500 mt-2">
          Geschätzte Fertigstellung: {new Date(job.estimated_completion).toLocaleTimeString('de-DE')}
        </p>
      )}

      {/* Error Message (nur bei failed) */}
      {status === 'failed' && jobStatus?.error_message && (
        <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          {jobStatus.error_message}
        </div>
      )}

      {/* Result (nur bei completed) */}
      {status === 'completed' && jobStatus?.result && (
        <>
          <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded">
            <p className="text-sm font-semibold text-green-900 mb-2">
              ✅ Fix generiert!
            </p>
            <button
              onClick={() => setShowResultModal(true)}
              className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-semibold rounded-lg transition-all shadow-md hover:shadow-lg transform hover:scale-[1.02] flex items-center gap-2"
            >
              <CheckCircle className="w-4 h-4" />
              Fix anzeigen & verwenden →
            </button>
          </div>
          
          {/* Result Modal */}
          <FixResultModal
            isOpen={showResultModal}
            onClose={() => setShowResultModal(false)}
            fixResult={parsedResult}
          />
        </>
      )}
    </div>
  );
};

