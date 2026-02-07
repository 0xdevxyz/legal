/**
 * Legal Action Required Widget
 * Zeigt ausstehende Benachrichtigungen und Handlungsbedarf
 * Mit Bestätigungs-Flow für Nutzer
 */

'use client';

import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  Bell, 
  CheckCircle, 
  X, 
  ExternalLink,
  Clock,
  Shield
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface LegalNotification {
  id: number;
  severity: 'critical' | 'warning' | 'high' | 'medium' | 'low' | 'info';
  status: string;
  action_required: boolean;
  action_deadline: string | null;
  sent_at: string | null;
  title: string;
  summary: string | null;
  source: string;
  url: string | null;
  published_date: string;
}

interface NotificationStats {
  pending: number;
  sent: number;
  confirmed: number;
  dismissed: number;
  critical_pending: number;
  action_required: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';

export default function LegalActionWidget() {
  const [notifications, setNotifications] = useState<LegalNotification[]>([]);
  const [stats, setStats] = useState<NotificationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNotification, setSelectedNotification] = useState<LegalNotification | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const [notifResponse, statsResponse] = await Promise.all([
        fetch(`${API_URL}/api/legal-notifications/pending`, {
          headers,
          credentials: 'include',
        }),
        fetch(`${API_URL}/api/legal-notifications/stats`, {
          headers,
          credentials: 'include',
        }),
      ]);

      if (notifResponse.ok) {
        const data = await notifResponse.json();
        setNotifications(data);
      }

      if (statsResponse.ok) {
        const data = await statsResponse.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to load notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (notification: LegalNotification) => {
    setSelectedNotification(notification);
    setIsModalOpen(true);
  };

  const confirmNotification = async () => {
    if (!selectedNotification) return;
    
    try {
      const token = localStorage.getItem('auth_token');
      const headers: HeadersInit = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(
        `${API_URL}/api/legal-notifications/confirm/${selectedNotification.id}`,
        {
          method: 'POST',
          headers,
          credentials: 'include',
        }
      );
      
      if (response.ok) {
        setNotifications(prev => prev.filter(n => n.id !== selectedNotification.id));
        setIsModalOpen(false);
        loadData();
      }
    } catch (error) {
      console.error('Failed to confirm notification:', error);
    }
  };

  const dismissNotification = async (id: number) => {
    try {
      const token = localStorage.getItem('auth_token');
      const headers: HeadersInit = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(
        `${API_URL}/api/legal-notifications/dismiss/${id}`,
        {
          method: 'POST',
          headers,
          credentials: 'include',
        }
      );
      
      if (response.ok) {
        setNotifications(prev => prev.filter(n => n.id !== id));
        loadData();
      }
    } catch (error) {
      console.error('Failed to dismiss notification:', error);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-500 text-white';
      case 'warning':
        return 'bg-orange-500 text-white';
      case 'high':
        return 'bg-yellow-500 text-black';
      case 'medium':
        return 'bg-blue-500 text-white';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  const getSeverityLabel = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'Kritisch';
      case 'warning':
        return 'Warnung';
      case 'high':
        return 'Wichtig';
      case 'medium':
        return 'Info';
      default:
        return 'Hinweis';
    }
  };

  if (loading) {
    return (
      <Card className="border-gray-700 bg-gray-800/50 backdrop-blur-sm">
        <CardContent className="pt-6">
          <div className="flex items-center justify-center h-32">
            <div className="w-8 h-8 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin" />
          </div>
        </CardContent>
      </Card>
    );
  }

  const hasCritical = stats?.critical_pending && stats.critical_pending > 0;
  const hasActions = stats?.action_required && stats.action_required > 0;

  return (
    <>
      <Card 
        className={`border-gray-700 backdrop-blur-sm transition-all duration-200 hover:shadow-lg ${
          hasCritical
            ? 'bg-gradient-to-br from-red-500/10 to-red-600/5 border-red-500/30'
            : hasActions
            ? 'bg-gradient-to-br from-orange-500/10 to-orange-600/5 border-orange-500/30'
            : 'bg-gray-800/50'
        }`}
      >
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-white">
            <div className="flex items-center gap-2">
              <Bell className="w-5 h-5 text-purple-400" />
              <span>Handlungsbedarf</span>
            </div>
            {hasCritical && (
              <Badge className="bg-red-500 text-white animate-pulse">
                {stats?.critical_pending} Dringend
              </Badge>
            )}
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          {stats && (
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="p-2 bg-gray-700/50 rounded-lg">
                <p className="text-2xl font-bold text-white">{stats.pending + stats.sent}</p>
                <p className="text-xs text-gray-400">Offen</p>
              </div>
              <div className="p-2 bg-gray-700/50 rounded-lg">
                <p className="text-2xl font-bold text-green-400">{stats.confirmed}</p>
                <p className="text-xs text-gray-400">Bestätigt</p>
              </div>
              <div className="p-2 bg-gray-700/50 rounded-lg">
                <p className="text-2xl font-bold text-orange-400">{stats.action_required}</p>
                <p className="text-xs text-gray-400">Aktionen</p>
              </div>
            </div>
          )}

          {notifications.length === 0 ? (
            <div className="text-center py-6">
              <Shield className="w-12 h-12 text-green-400 mx-auto mb-2 opacity-50" />
              <p className="text-sm text-gray-400">
                Keine ausstehenden Benachrichtigungen
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Sie sind auf dem neuesten Stand
              </p>
            </div>
          ) : (
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {notifications.slice(0, 5).map((notification) => (
                <div 
                  key={notification.id}
                  className={`p-3 rounded-lg border transition-all ${
                    notification.severity === 'critical'
                      ? 'bg-red-500/10 border-red-500/30'
                      : notification.severity === 'warning'
                      ? 'bg-orange-500/10 border-orange-500/30'
                      : 'bg-gray-700/50 border-gray-600'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge className={getSeverityColor(notification.severity)}>
                          {getSeverityLabel(notification.severity)}
                        </Badge>
                        {notification.action_required && (
                          <Badge variant="outline" className="text-orange-400 border-orange-400">
                            Aktion erforderlich
                          </Badge>
                        )}
                      </div>
                      <h4 className="font-medium text-white text-sm truncate">
                        {notification.title}
                      </h4>
                      <p className="text-xs text-gray-400 mt-1">
                        {notification.source} • {new Date(notification.published_date).toLocaleDateString('de-DE')}
                      </p>
                      {notification.action_deadline && (
                        <div className="flex items-center gap-1 mt-2 text-xs text-orange-400">
                          <Clock className="w-3 h-3" />
                          <span>
                            Frist: {new Date(notification.action_deadline).toLocaleDateString('de-DE')}
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="flex flex-col gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-7 w-7 p-0 text-green-400 hover:text-green-300 hover:bg-green-400/10"
                        onClick={() => handleConfirm(notification)}
                        title="Zur Kenntnis genommen"
                      >
                        <CheckCircle className="w-4 h-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-7 w-7 p-0 text-gray-400 hover:text-gray-300 hover:bg-gray-400/10"
                        onClick={() => dismissNotification(notification.id)}
                        title="Nicht relevant"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {notifications.length > 5 && (
            <Button variant="outline" className="w-full text-gray-300 border-gray-600">
              Alle {notifications.length} anzeigen
            </Button>
          )}
        </CardContent>
      </Card>

      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="bg-gray-800 border-gray-700 text-white max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-400" />
              Gesetzesänderung bestätigen
            </DialogTitle>
            <DialogDescription className="text-gray-400">
              Bitte bestätigen Sie, dass Sie diese Änderung zur Kenntnis genommen haben.
            </DialogDescription>
          </DialogHeader>
          
          {selectedNotification && (
            <div className="space-y-4">
              <div className="p-4 bg-gray-700/50 rounded-lg">
                <Badge className={`${getSeverityColor(selectedNotification.severity)} mb-2`}>
                  {getSeverityLabel(selectedNotification.severity)}
                </Badge>
                <h3 className="font-semibold text-white mb-2">
                  {selectedNotification.title}
                </h3>
                <p className="text-sm text-gray-300">
                  {selectedNotification.summary}
                </p>
                <p className="text-xs text-gray-400 mt-2">
                  Quelle: {selectedNotification.source}
                </p>
              </div>

              {selectedNotification.url && (
                <a 
                  href={selectedNotification.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-sm text-purple-400 hover:text-purple-300"
                >
                  <ExternalLink className="w-4 h-4" />
                  Originalartikel lesen
                </a>
              )}

              <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-3">
                <p className="text-sm text-orange-200">
                  Mit der Bestätigung erklären Sie, dass Sie diese Änderung zur Kenntnis 
                  genommen haben und ggf. notwendige Maßnahmen ergreifen werden.
                </p>
              </div>

              <div className="flex gap-3">
                <Button
                  variant="outline"
                  className="flex-1 border-gray-600 text-gray-300"
                  onClick={() => setIsModalOpen(false)}
                >
                  Abbrechen
                </Button>
                <Button
                  className="flex-1 bg-green-600 hover:bg-green-700"
                  onClick={confirmNotification}
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Zur Kenntnis genommen
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
