import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, formatDistanceToNow } from "date-fns";
import { de } from "date-fns/locale";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date) {
  return format(new Date(date), "dd.MM.yyyy HH:mm", { locale: de });
}

export function formatRelativeTime(date: string | Date) {
  return formatDistanceToNow(new Date(date), { 
    addSuffix: true, 
    locale: de 
  });
}

export function getRiskColor(severity: string) {
  switch (severity) {
    case 'critical':
      return 'text-red-400 bg-red-900/30 border-red-500/50';
    case 'medium':
      return 'text-yellow-400 bg-yellow-900/30 border-yellow-500/50';
    case 'low':
      return 'text-green-400 bg-green-900/30 border-green-500/50';
    default:
      return 'text-gray-400 bg-gray-900/30 border-gray-500/50';
  }
}

export function generateComplianceTrend(days: number): { date: string; score: number }[] {
  const data = [];
  let currentScore = 60;
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    
    const randomChange = (Math.random() - 0.5) * 4;
    const trendChange = 0.05;
    currentScore = Math.max(60, Math.min(100, currentScore + randomChange + trendChange));
    
    data.push({
      date: format(date, 'dd.MM'),
      score: Math.round(currentScore * 10) / 10
    });
  }
  
  return data;
}
