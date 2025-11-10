'use client';

import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { CheckCircle, Loader, AlertTriangle, ArrowRight } from 'lucide-react';

// API functions for workflow
const fetchCurrentStep = async () => {
  const { data } = await apiClient.get('/api/v2/workflow/current-step');
  return data.data;
};

const completeStep = async (payload: { step_id: string; validation_data?: any }) => {
  const { data } = await apiClient.post('/api/v2/workflow/complete-step', payload);
  return data.data;
};

const startJourney = async (payload: { website_url: string; skill_level: string }) => {
    const { data } = await apiClient.post('/api/v2/workflow/start-journey', payload);
    return data.data;
}

export default function JourneyPage() {
  const queryClient = useQueryClient();

  const { data: currentStep, isLoading, isError, error } = useQuery({
    queryKey: ['workflowStep'],
    queryFn: fetchCurrentStep,
  });

  const completeStepMutation = useMutation({
    mutationFn: completeStep,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflowStep'] });
    },
  });

  const startJourneyMutation = useMutation({
      mutationFn: startJourney,
      onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['workflowStep'] });
      }
  })

  const handleCompleteStep = () => {
    if (currentStep) {
      completeStepMutation.mutate({ step_id: currentStep.id, validation_data: { manual_completion: true } });
    }
  };

  const handleStartJourney = () => {
      // Replace with actual data, maybe from a form
      startJourneyMutation.mutate({ website_url: "https://example.com", skill_level: "beginner" });
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <Loader className="animate-spin h-12 w-12" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-red-500">
          <AlertTriangle className="h-12 w-12 mx-auto" />
          <p>Fehler beim Laden des Workflows: {error.message}</p>
        </div>
      </div>
    );
  }

  if (!currentStep) {
    return (
        <div className="flex flex-col justify-center items-center h-screen text-center">
            <CheckCircle className="h-16 w-16 text-green-500 mb-4" />
            <h1 className="text-2xl font-bold mb-2">Kein aktiver Workflow gefunden.</h1>
            <p className="text-gray-400 mb-6">Starten Sie eine neue Journey, um Ihre Compliance-Reise zu beginnen.</p>
            <Button onClick={handleStartJourney} disabled={startJourneyMutation.isPending}>
                {startJourneyMutation.isPending ? 'Starte...' : 'Neue Journey starten'}
            </Button>
        </div>
    )
  }

  return (
    <div className="container mx-auto p-8">
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="text-2xl font-bold">{currentStep.title}</CardTitle>
          <p className="text-gray-400">{currentStep.description}</p>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <h3 className="font-semibold">Anleitung:</h3>
            <ul className="list-disc list-inside space-y-2">
              {currentStep.instructions.map((instr: string, index: number) => (
                <li key={index}>{instr}</li>
              ))}
            </ul>
            <div className="text-sm text-gray-500">
              Geschätzte Zeit: {currentStep.estimated_time_minutes} Minuten
            </div>
          </div>
        </CardContent>
        <div className="p-6">
          <Button
            onClick={handleCompleteStep}
            disabled={completeStepMutation.isPending}
            className="w-full"
          >
            {completeStepMutation.isPending ? (
              <Loader className="animate-spin mr-2" />
            ) : (
              <CheckCircle className="mr-2" />
            )}
            Schritt als erledigt markieren
            <ArrowRight className="ml-auto" />
          </Button>
        </div>
      </Card>
    </div>
  );
}