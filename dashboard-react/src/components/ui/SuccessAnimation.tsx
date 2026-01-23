'use client';

import React, { useEffect, useState } from 'react';
import { CheckCircle, Sparkles, Trophy, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SuccessAnimationProps {
  message?: string;
  type?: 'default' | 'score' | 'fix' | 'achievement';
  show?: boolean;
  onComplete?: () => void;
  duration?: number;
}

/**
 * Success-Animation-Komponente für positive User-Feedback
 */
export const SuccessAnimation: React.FC<SuccessAnimationProps> = ({
  message = 'Erfolgreich!',
  type = 'default',
  show = false,
  onComplete,
  duration = 2000,
}) => {
  const [isVisible, setIsVisible] = useState(show);

  useEffect(() => {
    if (show) {
      setIsVisible(true);
      const timer = setTimeout(() => {
        setIsVisible(false);
        onComplete?.();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [show, duration, onComplete]);

  if (!isVisible) return null;

  const icons = {
    default: CheckCircle,
    score: Trophy,
    fix: Zap,
    achievement: Sparkles,
  };

  const Icon = icons[type];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none">
      <div
        className={cn(
          'bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-8 flex flex-col items-center gap-4',
          'animate-in fade-in zoom-in-95 duration-300',
          'border-2 border-green-500'
        )}
      >
        {/* Icon mit Animation */}
        <div className="relative">
          <div className="absolute inset-0 bg-green-500/20 rounded-full animate-ping" />
          <div className="relative bg-green-500/10 rounded-full p-4">
            <Icon className="w-12 h-12 text-green-500 animate-in zoom-in duration-500" />
          </div>
        </div>

        {/* Message */}
        <p className="text-xl font-semibold text-gray-900 dark:text-white text-center">
          {message}
        </p>

        {/* Progress Bar */}
        <div className="w-full h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500 rounded-full animate-in slide-in-from-left duration-2000"
            style={{ animationDuration: `${duration}ms` }}
          />
        </div>
      </div>
    </div>
  );
};

/**
 * Confetti-Animation für große Erfolge (z.B. 100% Score)
 */
export const ConfettiAnimation: React.FC<{ show?: boolean; onComplete?: () => void }> = ({
  show = false,
  onComplete,
}) => {
  const [isVisible, setIsVisible] = useState(show);

  useEffect(() => {
    if (show) {
      setIsVisible(true);
      const timer = setTimeout(() => {
        setIsVisible(false);
        onComplete?.();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [show, onComplete]);

  if (!isVisible) return null;

  const confetti = Array.from({ length: 50 }).map((_, i) => ({
    id: i,
    left: `${Math.random() * 100}%`,
    delay: Math.random() * 2,
    duration: 2 + Math.random() * 2,
    color: ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444'][
      Math.floor(Math.random() * 5)
    ],
  }));

  return (
    <div className="fixed inset-0 z-50 pointer-events-none overflow-hidden">
      {confetti.map((piece) => (
        <div
          key={piece.id}
          className="absolute w-3 h-3 rounded-full"
          style={{
            left: piece.left,
            top: '-10px',
            backgroundColor: piece.color,
            animation: `confetti-fall ${piece.duration}s ${piece.delay}s ease-out forwards`,
          }}
        />
      ))}
      <style jsx>{`
        @keyframes confetti-fall {
          to {
            transform: translateY(100vh) rotate(360deg);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  );
};

/**
 * Score-Animation für Compliance-Score-Verbesserungen
 */
export const ScoreAnimation: React.FC<{
  oldScore: number;
  newScore: number;
  show?: boolean;
  onComplete?: () => void;
}> = ({ oldScore, newScore, show = false, onComplete }) => {
  const [currentScore, setCurrentScore] = useState(oldScore);
  const [isVisible, setIsVisible] = useState(show);

  useEffect(() => {
    if (show) {
      setIsVisible(true);
      const duration = 1500;
      const steps = 30;
      const increment = (newScore - oldScore) / steps;
      let step = 0;

      const interval = setInterval(() => {
        step++;
        const nextScore = Math.min(oldScore + increment * step, newScore);
        setCurrentScore(Math.round(nextScore));

        if (step >= steps) {
          clearInterval(interval);
          setTimeout(() => {
            setIsVisible(false);
            onComplete?.();
          }, 500);
        }
      }, duration / steps);

      return () => clearInterval(interval);
    }
  }, [show, oldScore, newScore, onComplete]);

  if (!isVisible) return null;

  const improvement = newScore - oldScore;
  const isPerfect = newScore === 100;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-8 flex flex-col items-center gap-4 animate-in fade-in zoom-in-95 duration-300">
        {isPerfect && <ConfettiAnimation show={true} />}
        
        <div className="relative">
          <div className="absolute inset-0 bg-green-500/20 rounded-full animate-ping" />
          <div className="relative bg-green-500/10 rounded-full p-6">
            <Trophy className="w-16 h-16 text-green-500" />
          </div>
        </div>

        <div className="text-center">
          <p className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            {currentScore}%
          </p>
          {improvement > 0 && (
            <p className="text-lg text-green-600 dark:text-green-400 font-semibold">
              +{improvement} Punkte!
            </p>
          )}
          {isPerfect && (
            <p className="text-xl text-green-600 dark:text-green-400 font-bold mt-2">
              🎉 Perfekte Compliance erreicht!
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
