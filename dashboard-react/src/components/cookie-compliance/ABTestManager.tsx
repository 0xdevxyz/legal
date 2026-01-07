/**
 * A/B Test Manager Component
 * Manage and analyze cookie banner A/B tests
 */

import React, { useState, useEffect } from 'react';
import {
  FlaskConical,
  Play,
  Pause,
  StopCircle,
  Trophy,
  TrendingUp,
  TrendingDown,
  Users,
  CheckCircle,
  XCircle,
  Plus,
  Trash2,
  BarChart3,
  Loader2,
  AlertCircle,
  Info,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';

interface ABTestManagerProps {
  siteId: string;
  currentConfig: any;
}

interface ABTest {
  id: number;
  name: string;
  status: string;
  traffic_split: number;
  start_date: string | null;
  end_date: string | null;
  winner: string | null;
  total_impressions: number;
  created_at: string;
}

interface ABTestDetail {
  test: any;
  results: {
    variant_a: any;
    variant_b: any;
    improvement_percent: number;
    leading_variant: string | null;
  };
  statistics: {
    z_score: number;
    p_value: number;
    is_significant: boolean;
    sample_reached: boolean;
    confidence_level: number;
  };
}

const ABTestManager: React.FC<ABTestManagerProps> = ({ siteId, currentConfig }) => {
  const [tests, setTests] = useState<ABTest[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTest, setSelectedTest] = useState<ABTestDetail | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [creating, setCreating] = useState(false);
  
  // New test form
  const [newTest, setNewTest] = useState({
    name: '',
    description: '',
    hypothesis: '',
    trafficSplit: 50,
    variantBChanges: 'primary_color', // What to change in B
    variantBValue: '#10b981',
  });

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';

  useEffect(() => {
    loadTests();
  }, [siteId]);

  const loadTests = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/ab-tests/site/${siteId}`, {
        credentials: 'include',
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setTests(data.tests);
        }
      }
    } catch (error) {
      console.error('Error loading tests:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTestDetails = async (testId: number) => {
    try {
      const response = await fetch(`${API_URL}/api/ab-tests/${testId}`, {
        credentials: 'include',
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setSelectedTest(data);
        }
      }
    } catch (error) {
      console.error('Error loading test details:', error);
    }
  };

  const createTest = async () => {
    try {
      setCreating(true);
      
      // Build variant configs
      const variantA = { ...currentConfig };
      const variantB = { ...currentConfig };
      
      // Apply change to variant B
      variantB[newTest.variantBChanges] = newTest.variantBValue;
      
      const response = await fetch(`${API_URL}/api/ab-tests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          site_id: siteId,
          name: newTest.name,
          description: newTest.description,
          hypothesis: newTest.hypothesis,
          variant_a_config: variantA,
          variant_b_config: variantB,
          traffic_split: newTest.trafficSplit,
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setShowCreateDialog(false);
          loadTests();
          // Reset form
          setNewTest({
            name: '',
            description: '',
            hypothesis: '',
            trafficSplit: 50,
            variantBChanges: 'primary_color',
            variantBValue: '#10b981',
          });
        }
      }
    } catch (error) {
      console.error('Error creating test:', error);
    } finally {
      setCreating(false);
    }
  };

  const startTest = async (testId: number) => {
    try {
      const response = await fetch(`${API_URL}/api/ab-tests/${testId}/start`, {
        method: 'POST',
        credentials: 'include',
      });
      
      if (response.ok) {
        loadTests();
        if (selectedTest?.test.id === testId) {
          loadTestDetails(testId);
        }
      }
    } catch (error) {
      console.error('Error starting test:', error);
    }
  };

  const stopTest = async (testId: number, winner?: string) => {
    try {
      const response = await fetch(`${API_URL}/api/ab-tests/${testId}/stop?winner=${winner || ''}`, {
        method: 'POST',
        credentials: 'include',
      });
      
      if (response.ok) {
        loadTests();
        if (selectedTest?.test.id === testId) {
          loadTestDetails(testId);
        }
      }
    } catch (error) {
      console.error('Error stopping test:', error);
    }
  };

  const deleteTest = async (testId: number) => {
    if (!confirm('Sind Sie sicher, dass Sie diesen Test loeschen moechten?')) return;
    
    try {
      const response = await fetch(`${API_URL}/api/ab-tests/${testId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      
      if (response.ok) {
        loadTests();
        if (selectedTest?.test.id === testId) {
          setSelectedTest(null);
        }
      }
    } catch (error) {
      console.error('Error deleting test:', error);
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      draft: 'bg-gray-500',
      running: 'bg-green-500',
      paused: 'bg-yellow-500',
      completed: 'bg-blue-500',
      cancelled: 'bg-red-500',
    };
    
    const labels: Record<string, string> = {
      draft: 'Entwurf',
      running: 'Aktiv',
      paused: 'Pausiert',
      completed: 'Abgeschlossen',
      cancelled: 'Abgebrochen',
    };
    
    return (
      <Badge className={`${styles[status] || 'bg-gray-500'} text-white`}>
        {labels[status] || status}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-orange-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <FlaskConical className="w-5 h-5 text-orange-500" />
            A/B Testing
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            Testen Sie verschiedene Banner-Varianten zur Optimierung der Opt-In-Rate
          </p>
        </div>
        
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-orange-500 hover:bg-orange-600">
              <Plus className="w-4 h-4 mr-2" />
              Neuer Test
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Neuen A/B Test erstellen</DialogTitle>
              <DialogDescription>
                Erstellen Sie einen Test, um verschiedene Banner-Konfigurationen zu vergleichen.
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Test-Name</Label>
                <Input
                  id="name"
                  value={newTest.name}
                  onChange={(e) => setNewTest({ ...newTest, name: e.target.value })}
                  placeholder="z.B. Button-Farbe Test"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="hypothesis">Hypothese</Label>
                <Textarea
                  id="hypothesis"
                  value={newTest.hypothesis}
                  onChange={(e) => setNewTest({ ...newTest, hypothesis: e.target.value })}
                  placeholder="z.B. Ein gruener Button fuehrt zu hoeherer Akzeptanzrate"
                  rows={2}
                />
              </div>
              
              <div className="space-y-2">
                <Label>Was wird getestet?</Label>
                <Select
                  value={newTest.variantBChanges}
                  onValueChange={(v) => setNewTest({ ...newTest, variantBChanges: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="primary_color">Primaerfarbe</SelectItem>
                    <SelectItem value="layout">Layout</SelectItem>
                    <SelectItem value="button_style">Button-Stil</SelectItem>
                    <SelectItem value="position">Position</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              {newTest.variantBChanges === 'primary_color' && (
                <div className="space-y-2">
                  <Label htmlFor="color">Variante B Farbe</Label>
                  <div className="flex gap-2">
                    <Input
                      id="color"
                      type="color"
                      value={newTest.variantBValue}
                      onChange={(e) => setNewTest({ ...newTest, variantBValue: e.target.value })}
                      className="w-16 h-10"
                    />
                    <Input
                      value={newTest.variantBValue}
                      onChange={(e) => setNewTest({ ...newTest, variantBValue: e.target.value })}
                      className="flex-1"
                    />
                  </div>
                </div>
              )}
              
              <div className="space-y-2">
                <Label>Traffic-Verteilung: {newTest.trafficSplit}% / {100 - newTest.trafficSplit}%</Label>
                <Slider
                  value={[newTest.trafficSplit]}
                  onValueChange={([v]) => setNewTest({ ...newTest, trafficSplit: v })}
                  min={10}
                  max={90}
                  step={5}
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>Variante A (Control)</span>
                  <span>Variante B (Test)</span>
                </div>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                Abbrechen
              </Button>
              <Button 
                onClick={createTest} 
                disabled={!newTest.name || creating}
                className="bg-orange-500 hover:bg-orange-600"
              >
                {creating ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Test erstellen
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Active Test Alert */}
      {tests.find(t => t.status === 'running') && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="flex items-center gap-4 py-4">
            <div className="p-2 bg-green-500 rounded-full">
              <Play className="w-4 h-4 text-white" />
            </div>
            <div className="flex-1">
              <p className="font-medium text-green-800">
                Test aktiv: {tests.find(t => t.status === 'running')?.name}
              </p>
              <p className="text-sm text-green-600">
                {tests.find(t => t.status === 'running')?.total_impressions.toLocaleString()} Impressionen
              </p>
            </div>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => {
                const test = tests.find(t => t.status === 'running');
                if (test) loadTestDetails(test.id);
              }}
            >
              Details anzeigen
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Tests List */}
      {tests.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FlaskConical className="w-12 h-12 text-gray-300 mb-4" />
            <p className="text-gray-500 mb-4">Noch keine A/B Tests erstellt</p>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Ersten Test erstellen
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {tests.map((test) => (
            <Card 
              key={test.id}
              className={`cursor-pointer transition-all hover:shadow-md ${
                selectedTest?.test.id === test.id ? 'ring-2 ring-orange-500' : ''
              }`}
              onClick={() => loadTestDetails(test.id)}
            >
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`p-2 rounded-full ${
                      test.status === 'running' ? 'bg-green-100' : 
                      test.status === 'completed' ? 'bg-blue-100' : 'bg-gray-100'
                    }`}>
                      {test.status === 'running' ? (
                        <Play className="w-4 h-4 text-green-600" />
                      ) : test.status === 'completed' ? (
                        <CheckCircle className="w-4 h-4 text-blue-600" />
                      ) : (
                        <FlaskConical className="w-4 h-4 text-gray-600" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium">{test.name}</h3>
                        {getStatusBadge(test.status)}
                        {test.winner && (
                          <Badge className="bg-yellow-500 text-white">
                            <Trophy className="w-3 h-3 mr-1" />
                            Gewinner: {test.winner}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-500">
                        {test.total_impressions.toLocaleString()} Impressionen
                        {test.start_date && ` • Gestartet: ${new Date(test.start_date).toLocaleDateString('de-DE')}`}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                    {test.status === 'draft' && (
                      <>
                        <Button 
                          size="sm" 
                          onClick={() => startTest(test.id)}
                          className="bg-green-500 hover:bg-green-600"
                        >
                          <Play className="w-4 h-4 mr-1" />
                          Starten
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => deleteTest(test.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </>
                    )}
                    {test.status === 'running' && (
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => stopTest(test.id)}
                      >
                        <StopCircle className="w-4 h-4 mr-1" />
                        Beenden
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Test Details */}
      {selectedTest && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>{selectedTest.test.name}</span>
              {getStatusBadge(selectedTest.test.status)}
            </CardTitle>
            {selectedTest.test.hypothesis && (
              <CardDescription>{selectedTest.test.hypothesis}</CardDescription>
            )}
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="results">
              <TabsList>
                <TabsTrigger value="results">Ergebnisse</TabsTrigger>
                <TabsTrigger value="statistics">Statistik</TabsTrigger>
                <TabsTrigger value="config">Konfiguration</TabsTrigger>
              </TabsList>
              
              <TabsContent value="results" className="space-y-4 mt-4">
                {/* Results Comparison */}
                <div className="grid grid-cols-2 gap-4">
                  {/* Variant A */}
                  <Card className={selectedTest.results.leading_variant === 'A' ? 'ring-2 ring-green-500' : ''}>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base flex items-center justify-between">
                        <span>Variante A (Control)</span>
                        {selectedTest.results.leading_variant === 'A' && (
                          <TrendingUp className="w-4 h-4 text-green-500" />
                        )}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Impressionen</span>
                          <span className="font-medium">
                            {selectedTest.results.variant_a.impressions.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Akzeptiert</span>
                          <span className="font-medium">
                            {selectedTest.results.variant_a.accepted_all.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between text-lg">
                          <span className="text-gray-500">Rate</span>
                          <span className="font-bold text-green-600">
                            {selectedTest.results.variant_a.rate}%
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  
                  {/* Variant B */}
                  <Card className={selectedTest.results.leading_variant === 'B' ? 'ring-2 ring-green-500' : ''}>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base flex items-center justify-between">
                        <span>Variante B (Test)</span>
                        {selectedTest.results.leading_variant === 'B' && (
                          <TrendingUp className="w-4 h-4 text-green-500" />
                        )}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Impressionen</span>
                          <span className="font-medium">
                            {selectedTest.results.variant_b.impressions.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Akzeptiert</span>
                          <span className="font-medium">
                            {selectedTest.results.variant_b.accepted_all.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between text-lg">
                          <span className="text-gray-500">Rate</span>
                          <span className="font-bold text-green-600">
                            {selectedTest.results.variant_b.rate}%
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
                
                {/* Improvement */}
                <Card className={selectedTest.results.improvement_percent > 0 ? 'bg-green-50' : 'bg-red-50'}>
                  <CardContent className="py-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {selectedTest.results.improvement_percent > 0 ? (
                          <TrendingUp className="w-5 h-5 text-green-600" />
                        ) : (
                          <TrendingDown className="w-5 h-5 text-red-600" />
                        )}
                        <span className="font-medium">Veraenderung (B vs A)</span>
                      </div>
                      <span className={`text-xl font-bold ${
                        selectedTest.results.improvement_percent > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {selectedTest.results.improvement_percent > 0 ? '+' : ''}
                        {selectedTest.results.improvement_percent}%
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
              
              <TabsContent value="statistics" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <Card>
                    <CardContent className="py-4">
                      <div className="text-center">
                        <p className="text-gray-500 text-sm">Z-Score</p>
                        <p className="text-2xl font-bold">{selectedTest.statistics.z_score}</p>
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="py-4">
                      <div className="text-center">
                        <p className="text-gray-500 text-sm">P-Wert</p>
                        <p className="text-2xl font-bold">{selectedTest.statistics.p_value}</p>
                      </div>
                    </CardContent>
                  </Card>
                </div>
                
                <Card className={selectedTest.statistics.is_significant ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'}>
                  <CardContent className="py-4">
                    <div className="flex items-center gap-3">
                      {selectedTest.statistics.is_significant ? (
                        <CheckCircle className="w-6 h-6 text-green-600" />
                      ) : (
                        <AlertCircle className="w-6 h-6 text-yellow-600" />
                      )}
                      <div>
                        <p className="font-medium">
                          {selectedTest.statistics.is_significant 
                            ? 'Statistisch signifikant!' 
                            : 'Noch nicht signifikant'}
                        </p>
                        <p className="text-sm text-gray-500">
                          Konfidenz-Level: {(selectedTest.statistics.confidence_level * 100).toFixed(0)}%
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                
                {!selectedTest.statistics.sample_reached && (
                  <Card className="bg-blue-50 border-blue-200">
                    <CardContent className="py-4">
                      <div className="flex items-center gap-3">
                        <Info className="w-6 h-6 text-blue-600" />
                        <div>
                          <p className="font-medium text-blue-800">
                            Mindest-Stichprobe noch nicht erreicht
                          </p>
                          <p className="text-sm text-blue-600">
                            Warten Sie auf mehr Impressionen fuer zuverlaessige Ergebnisse.
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </TabsContent>
              
              <TabsContent value="config" className="mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base">Variante A</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto max-h-48">
                        {JSON.stringify(selectedTest.test.variant_a_config, null, 2)}
                      </pre>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base">Variante B</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto max-h-48">
                        {JSON.stringify(selectedTest.test.variant_b_config, null, 2)}
                      </pre>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
            </Tabs>
            
            {/* Actions */}
            {selectedTest.test.status === 'running' && selectedTest.statistics.is_significant && (
              <div className="mt-6 flex gap-2 justify-end">
                <Button 
                  variant="outline"
                  onClick={() => stopTest(selectedTest.test.id, 'A')}
                >
                  <Trophy className="w-4 h-4 mr-2" />
                  A als Gewinner
                </Button>
                <Button 
                  className="bg-green-500 hover:bg-green-600"
                  onClick={() => stopTest(selectedTest.test.id, 'B')}
                >
                  <Trophy className="w-4 h-4 mr-2" />
                  B als Gewinner
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ABTestManager;

