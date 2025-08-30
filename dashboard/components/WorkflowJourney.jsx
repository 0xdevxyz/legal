/**
 * Complyo Workflow Journey Component
 * Complete User Journey from Registration to 100% Compliance
 */

import React, { useState, useEffect } from 'react';
import { 
  ArrowRight, 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  Trophy,
  BookOpen,
  Settings,
  Shield,
  Wrench,
  Play,
  Download
} from 'lucide-react';

const WorkflowJourney = () => {
  const [currentJourney, setCurrentJourney] = useState(null);
  const [currentStep, setCurrentStep] = useState(null);
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Skill level options
  const skillLevels = [
    { value: 'absolute_beginner', label: 'Absoluter Anfänger', description: 'Ich bin komplett neu bei Websites' },
    { value: 'beginner', label: 'Anfänger', description: 'Grundkenntnisse vorhanden' },
    { value: 'intermediate', label: 'Fortgeschritten', description: 'Ich kenne mich etwas aus' },
    { value: 'advanced', label: 'Experte', description: 'Ich bin technisch versiert' }
  ];

  // Workflow stage icons and descriptions
  const stageInfo = {
    'onboarding': {
      icon: BookOpen,
      title: 'Einführung',
      description: 'Lernen Sie Complyo kennen',
      color: 'bg-blue-500'
    },
    'website_analysis': {
      icon: Settings,
      title: 'Website-Analyse',
      description: 'KI analysiert Ihre Website',
      color: 'bg-yellow-500'
    },
    'guided_optimization': {
      icon: Wrench,
      title: 'Optimierung',
      description: 'Geführte Problemlösung',
      color: 'bg-orange-500'
    },
    'compliance_verification': {
      icon: Shield,
      title: 'Verifizierung',
      description: 'Compliance-Prüfung',
      color: 'bg-green-500'
    },
    'maintenance': {
      icon: Trophy,
      title: 'Wartung',
      description: 'Dauerhafter Schutz',
      color: 'bg-purple-500'
    }
  };

  // API Base URL
  const API_BASE = process.env.NODE_ENV === 'development' ? 'http://localhost:8000' : '';

  // Get auth token
  const getAuthToken = () => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('token') || sessionStorage.getItem('auth_token');
    }
    return null;
  };

  // Start new journey
  const startJourney = async (websiteUrl, skillLevel) => {
    setLoading(true);
    setError(null);
    
    try {
      const token = getAuthToken();
      const response = await fetch(`${API_BASE}/api/workflow/start-journey`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify({
          website_url: websiteUrl,
          skill_level: skillLevel
        })
      });
      
      const result = await response.json();
      
      if (result.status === 'success') {
        setCurrentJourney(result.journey);
        await fetchCurrentStep();
        await fetchProgress();
      } else {
        setError(result.detail || 'Journey konnte nicht gestartet werden');
      }
    } catch (err) {
      setError(`Fehler beim Starten: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Fetch current step
  const fetchCurrentStep = async () => {
    try {
      const token = getAuthToken();
      const response = await fetch(`${API_BASE}/api/workflow/current-step`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });
      
      const result = await response.json();
      
      if (result.status === 'success') {
        setCurrentStep(result.current_step);
      }
    } catch (err) {
      console.error('Error fetching current step:', err);
    }
  };

  // Fetch progress
  const fetchProgress = async () => {
    try {
      const token = getAuthToken();
      const response = await fetch(`${API_BASE}/api/workflow/progress`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });
      
      const result = await response.json();
      
      if (result.status === 'success') {
        setProgress(result.progress);
      }
    } catch (err) {
      console.error('Error fetching progress:', err);
    }
  };

  // Complete current step
  const completeStep = async (validationData) => {
    if (!currentStep) return;
    
    setLoading(true);
    
    try {
      const token = getAuthToken();
      const response = await fetch(`${API_BASE}/api/workflow/complete-step`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify({
          step_id: currentStep.id,
          validation_data: validationData
        })
      });
      
      const result = await response.json();
      
      if (result.status === 'completed') {
        // Show success message
        if (result.congratulation_message) {
          alert(result.congratulation_message);
        }
        
        // Refresh current step and progress
        await fetchCurrentStep();
        await fetchProgress();
        
        // Check if journey is complete
        if (result.journey_completed) {
          alert(result.celebration_message);
        }
      } else if (result.status === 'validation_failed') {
        setError(result.validation_message || 'Validierung fehlgeschlagen');
      }
    } catch (err) {
      setError(`Fehler beim Abschließen: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Load journey on component mount
  useEffect(() => {
    fetchCurrentStep();
    fetchProgress();
  }, []);

  // Journey Start Form Component
  const JourneyStartForm = () => {
    const [websiteUrl, setWebsiteUrl] = useState('');
    const [skillLevel, setSkillLevel] = useState('beginner');
    
    const handleSubmit = (e) => {
      e.preventDefault();
      if (websiteUrl.trim()) {
        startJourney(websiteUrl.trim(), skillLevel);
      }
    };
    
    return (
      <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
        <div className="text-center mb-6">
          <h2 className="text-3xl font-bold text-gray-800 mb-2">
            🚀 Starten Sie Ihre Compliance-Reise
          </h2>
          <p className="text-gray-600">
            In wenigen Schritten zur 100% rechtssicheren Website
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Website-URL
            </label>
            <input
              type="url"
              value={websiteUrl}
              onChange={(e) => setWebsiteUrl(e.target.value)}
              placeholder="https://ihre-website.de"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Ihr Erfahrungslevel
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {skillLevels.map((level) => (
                <label
                  key={level.value}
                  className={`cursor-pointer p-4 border-2 rounded-lg transition-all ${
                    skillLevel === level.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="skillLevel"
                    value={level.value}
                    checked={skillLevel === level.value}
                    onChange={(e) => setSkillLevel(e.target.value)}
                    className="sr-only"
                  />
                  <div className="font-medium text-gray-800">{level.label}</div>
                  <div className="text-sm text-gray-600">{level.description}</div>
                </label>
              ))}
            </div>
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-4 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2" />
                Journey wird gestartet...
              </>
            ) : (
              <>
                Journey starten
                <ArrowRight className="ml-2 h-5 w-5" />
              </>
            )}
          </button>
        </form>
      </div>
    );
  };

  // Progress Bar Component
  const ProgressBar = ({ progress }) => {
    if (!progress) return null;
    
    return (
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-800">Fortschritt</h3>
          <span className="text-2xl font-bold text-blue-600">
            {Math.round(progress.progress_percentage || 0)}%
          </span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
          <div
            className="bg-blue-600 h-3 rounded-full transition-all duration-500"
            style={{ width: `${progress.progress_percentage || 0}%` }}
          />
        </div>
        
        <div className="flex justify-between text-sm text-gray-600">
          <span>{progress.completed_steps || 0} von {progress.total_steps || 13} Schritten</span>
          <span>{progress.estimated_time_remaining || 'Berechnung läuft...'}</span>
        </div>
        
        {/* Stage Progress */}
        {progress.stage_progress && (
          <div className="mt-4 space-y-2">
            <h4 className="text-sm font-medium text-gray-700">Phasen-Fortschritt:</h4>
            {Object.entries(progress.stage_progress).map(([stage, stageData]) => {
              const stageInfo_local = stageInfo[stage];
              return (
                <div key={stage} className="flex items-center space-x-3">
                  <div className={`p-1 rounded ${stageInfo_local?.color || 'bg-gray-500'}`}>
                    {stageInfo_local?.icon && React.createElement(stageInfo_local.icon, {
                      className: "h-4 w-4 text-white"
                    })}
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between text-xs">
                      <span>{stageInfo_local?.title || stage}</span>
                      <span>{stageData.completed}/{stageData.total}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-1.5">
                      <div
                        className="bg-blue-500 h-1.5 rounded-full"
                        style={{ width: `${stageData.percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  // Current Step Component
  const CurrentStep = ({ step }) => {
    if (!step) return null;
    
    const StageIcon = stageInfo[step.stage]?.icon || BookOpen;
    const stageData = stageInfo[step.stage] || {};
    
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center mb-4">
          <div className={`p-3 rounded-full ${stageData.color} mr-4`}>
            <StageIcon className="h-6 w-6 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-semibold text-gray-800">{step.title}</h3>
            <p className="text-gray-600">{step.description}</p>
          </div>
        </div>
        
        <div className="space-y-4">
          <div className="flex items-center text-sm text-gray-600">
            <Clock className="h-4 w-4 mr-2" />
            Geschätzte Zeit: {step.estimated_time_minutes} Minuten
          </div>
          
          <div>
            <h4 className="font-medium text-gray-800 mb-2">Anweisungen:</h4>
            <ul className="space-y-2">
              {step.instructions?.map((instruction, index) => (
                <li key={index} className="flex items-start">
                  <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium mr-3 mt-0.5">
                    {index + 1}
                  </span>
                  <span className="text-gray-700">{instruction}</span>
                </li>
              ))}
            </ul>
          </div>
          
          {step.requires_technical_knowledge && (
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
              <div className="flex">
                <AlertCircle className="h-5 w-5 text-yellow-400 mr-2" />
                <p className="text-sm text-yellow-700">
                  Dieser Schritt erfordert technische Kenntnisse. 
                  Bei Problemen steht Ihnen unser Support zur Verfügung.
                </p>
              </div>
            </div>
          )}
          
          {/* Visual Aids */}
          {step.visual_aids && step.visual_aids.length > 0 && (
            <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
              <h5 className="font-medium text-blue-800 mb-2">Hilfreiche Materialien:</h5>
              <ul className="space-y-1">
                {step.visual_aids.map((aid, index) => (
                  <li key={index} className="flex items-center text-blue-700">
                    {aid.includes('.mp4') ? (
                      <Play className="h-4 w-4 mr-2" />
                    ) : (
                      <Download className="h-4 w-4 mr-2" />
                    )}
                    <span className="text-sm">{aid}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          <div className="flex space-x-3 pt-4">
            <button
              onClick={() => completeStep({ manual_completion: true })}
              disabled={loading}
              className="flex-1 bg-green-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 flex items-center justify-center"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
              ) : (
                <>
                  <CheckCircle className="h-5 w-5 mr-2" />
                  Schritt abschließen
                </>
              )}
            </button>
            
            <button
              onClick={() => setError('Brauchen Sie Hilfe? Kontaktieren Sie unseren Support!')}
              className="px-6 py-3 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50"
            >
              Hilfe benötigt
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Journey Complete Component
  const JourneyComplete = () => (
    <div className="text-center p-8 bg-gradient-to-br from-green-50 to-blue-50 rounded-lg">
      <Trophy className="h-16 w-16 text-yellow-500 mx-auto mb-4" />
      <h2 className="text-3xl font-bold text-gray-800 mb-2">
        🎉 Herzlichen Glückwunsch!
      </h2>
      <p className="text-xl text-gray-600 mb-6">
        Ihre Website ist jetzt 100% compliant!
      </p>
      <div className="space-y-4">
        <button className="bg-blue-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-700 mr-4">
          Zertifikat herunterladen
        </button>
        <button 
          onClick={() => window.location.href = '/dashboard'}
          className="bg-gray-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-gray-700"
        >
          Dashboard öffnen
        </button>
      </div>
    </div>
  );

  // Error Display
  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
            <p className="text-red-700">{error}</p>
          </div>
        </div>
        <button
          onClick={() => setError(null)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Erneut versuchen
        </button>
      </div>
    );
  }

  // Main Render
  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-800 mb-4">
          🛡️ Complyo Journey
        </h1>
        <p className="text-xl text-gray-600">
          Ihre persönliche Reise zur 100% rechtssicheren Website
        </p>
      </div>

      {/* Progress Bar */}
      <ProgressBar progress={progress} />

      {/* Main Content */}
      {!currentJourney && !currentStep && <JourneyStartForm />}
      {currentStep && !progress?.journey_completed && <CurrentStep step={currentStep} />}
      {progress?.actual_completion && <JourneyComplete />}
    </div>
  );
};

export default WorkflowJourney;