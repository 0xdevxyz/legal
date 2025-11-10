'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, BookOpen, Check } from 'lucide-react';

interface GuideFixStepProps {
  fixData: {
    title: string;
    description: string;
    guide_steps: string[];
    integration_instructions: string;
  };
  onComplete: () => void;
}

export const GuideFixStep: React.FC<GuideFixStepProps> = ({ fixData, onComplete }) => {
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  
  const toggleStep = (index: number) => {
    setCompletedSteps(prev => 
      prev.includes(index) 
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  };
  
  const allStepsCompleted = completedSteps.length === fixData.guide_steps.length;
  
  return (
    <Card className="border-orange-200 shadow-md">
      <CardHeader className="bg-gradient-to-r from-orange-50 to-amber-50">
        <CardTitle className="flex items-center gap-3 text-xl">
          <BookOpen className="w-6 h-6 text-orange-600" />
          {fixData.title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 mt-4">
        <p className="text-gray-700">{fixData.description}</p>
        
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
          <h4 className="font-semibold text-orange-900 mb-3">📖 Schritt-für-Schritt-Anleitung:</h4>
          <div className="space-y-3">
            {fixData.guide_steps.map((step, index) => (
              <div 
                key={index}
                className={`flex items-start gap-3 p-3 rounded-lg border transition-all cursor-pointer ${
                  completedSteps.includes(index)
                    ? 'bg-green-50 border-green-300'
                    : 'bg-white border-gray-200 hover:border-orange-300'
                }`}
                onClick={() => toggleStep(index)}
              >
                <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center mt-0.5 ${
                  completedSteps.includes(index)
                    ? 'bg-green-600 text-white'
                    : 'bg-orange-200 text-orange-700 font-semibold'
                }`}>
                  {completedSteps.includes(index) ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    <span className="text-sm">{index + 1}</span>
                  )}
                </div>
                <p className={`text-sm flex-1 ${
                  completedSteps.includes(index) ? 'text-green-900 line-through' : 'text-gray-800'
                }`}>
                  {step}
                </p>
              </div>
            ))}
          </div>
        </div>
        
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-semibold text-blue-900 mb-2">💡 Zusätzliche Hinweise:</h4>
          <p className="text-sm text-blue-800">{fixData.integration_instructions}</p>
        </div>
        
        {allStepsCompleted && (
          <div className="bg-green-50 border-2 border-green-300 rounded-lg p-4 animate-pulse">
            <p className="text-center text-green-900 font-semibold flex items-center justify-center gap-2">
              <CheckCircle className="w-5 h-5" />
              Alle Schritte abgeschlossen! Sie können fortfahren.
            </p>
          </div>
        )}
        
        <div className="flex justify-end mt-6">
          <Button 
            onClick={onComplete}
            disabled={!allStepsCompleted}
            className={`${
              allStepsCompleted
                ? 'bg-gradient-to-r from-green-500 to-teal-600 hover:from-green-600 hover:to-teal-700'
                : 'bg-gray-300 cursor-not-allowed'
            } text-white`}
          >
            <CheckCircle className="w-4 h-4 mr-2" />
            Anleitung befolgt, weiter
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

