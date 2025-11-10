'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight, CheckCircle2, Circle, AlertCircle } from 'lucide-react'
import { CodeSnippetWithCopy } from './CodeSnippetWithCopy'

interface Step {
  number: number
  title: string
  description: string
  visual_hint?: string
  code?: string
  code_language?: string
}

interface TroubleshootingItem {
  problem: string
  solution: string
}

interface StepByStepGuideProps {
  steps: Step[]
  code?: string
  codeLanguage?: string
  placement?: string
  testInstructions?: string[]
  troubleshooting?: TroubleshootingItem[]
  estimatedTime?: string
  difficulty?: string
}

export function StepByStepGuide({
  steps,
  code,
  codeLanguage = 'html',
  placement,
  testInstructions = [],
  troubleshooting = [],
  estimatedTime,
  difficulty
}: StepByStepGuideProps) {
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set())
  const [expandedStep, setExpandedStep] = useState<number | null>(null)
  const [troubleshootingOpen, setTroubleshootingOpen] = useState(false)

  const toggleStepCompletion = (stepNumber: number) => {
    const newCompleted = new Set(completedSteps)
    if (newCompleted.has(stepNumber)) {
      newCompleted.delete(stepNumber)
    } else {
      newCompleted.add(stepNumber)
    }
    setCompletedSteps(newCompleted)
  }

  const toggleStepExpand = (stepNumber: number) => {
    setExpandedStep(expandedStep === stepNumber ? null : stepNumber)
  }

  const progressPercentage = (completedSteps.size / steps.length) * 100

  return (
    <div className="space-y-6">
      {/* Header mit Progress */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-2xl font-bold">Schritt-für-Schritt Anleitung</h3>
            <p className="text-blue-100 mt-1">
              {completedSteps.size} von {steps.length} Schritten abgeschlossen
            </p>
          </div>
          <div className="text-right">
            {estimatedTime && (
              <p className="text-sm text-blue-100">⏱️ {estimatedTime}</p>
            )}
            {difficulty && (
              <p className="text-sm text-blue-100 mt-1">📊 {difficulty}</p>
            )}
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="w-full bg-blue-800 rounded-full h-3 overflow-hidden">
          <div
            className="bg-gradient-to-r from-green-400 to-green-500 h-full transition-all duration-500 ease-out"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>

      {/* Steps List */}
      <div className="space-y-4">
        {steps.map((step) => {
          const isCompleted = completedSteps.has(step.number)
          const isExpanded = expandedStep === step.number

          return (
            <div
              key={step.number}
              className={`
                border-2 rounded-lg transition-all duration-200
                ${isCompleted 
                  ? 'border-green-500 bg-green-50' 
                  : 'border-gray-300 bg-white hover:border-blue-400'
                }
              `}
            >
              {/* Step Header */}
              <button
                onClick={() => toggleStepExpand(step.number)}
                className="w-full px-6 py-4 flex items-center gap-4 text-left"
              >
                {/* Checkbox */}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    toggleStepCompletion(step.number)
                  }}
                  className="flex-shrink-0"
                >
                  {isCompleted ? (
                    <CheckCircle2 className="w-8 h-8 text-green-600" />
                  ) : (
                    <Circle className="w-8 h-8 text-gray-400 hover:text-blue-500" />
                  )}
                </button>

                {/* Step Number */}
                <div
                  className={`
                    flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center font-bold
                    ${isCompleted 
                      ? 'bg-green-600 text-white' 
                      : 'bg-blue-600 text-white'
                    }
                  `}
                >
                  {step.number}
                </div>

                {/* Step Title */}
                <div className="flex-1 min-w-0">
                  <h4 className="font-semibold text-lg text-gray-900">{step.title}</h4>
                  {!isExpanded && (
                    <p className="text-sm text-gray-600 truncate mt-1">{step.description}</p>
                  )}
                </div>

                {/* Expand Icon */}
                {isExpanded ? (
                  <ChevronDown className="w-5 h-5 text-gray-500 flex-shrink-0" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-gray-500 flex-shrink-0" />
                )}
              </button>

              {/* Step Content (Expanded) */}
              {isExpanded && (
                <div className="px-6 pb-6 space-y-4 border-t-2 border-gray-200 pt-4">
                  <p className="text-gray-700 leading-relaxed">{step.description}</p>
                  
                  {step.visual_hint && (
                    <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                      <p className="text-sm text-blue-800">
                        <strong>💡 Tipp:</strong> {step.visual_hint}
                      </p>
                    </div>
                  )}
                  
                  {step.code && (
                    <div>
                      <h5 className="font-semibold text-gray-900 mb-2">Code für diesen Schritt:</h5>
                      <CodeSnippetWithCopy 
                        code={step.code} 
                        language={step.code_language || codeLanguage}
                      />
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Main Code Block */}
      {code && (
        <div className="space-y-3">
          <h4 className="text-lg font-semibold text-gray-900">📝 Vollständiger Code</h4>
          {placement && (
            <p className="text-sm text-gray-600">
              <strong>Wo einfügen:</strong> {placement}
            </p>
          )}
          <CodeSnippetWithCopy code={code} language={codeLanguage} />
        </div>
      )}

      {/* Test Instructions */}
      {testInstructions.length > 0 && (
        <div className="bg-green-50 border-2 border-green-300 rounded-lg p-6">
          <h4 className="text-lg font-semibold text-green-900 mb-3 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5" />
            So testen Sie die Lösung
          </h4>
          <ol className="space-y-2">
            {testInstructions.map((instruction, idx) => (
              <li key={idx} className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-green-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                  {idx + 1}
                </span>
                <span className="text-green-900">{instruction}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Troubleshooting */}
      {troubleshooting.length > 0 && (
        <details
          className="bg-yellow-50 border-2 border-yellow-300 rounded-lg overflow-hidden"
          open={troubleshootingOpen}
          onToggle={(e) => setTroubleshootingOpen((e.target as HTMLDetailsElement).open)}
        >
          <summary className="px-6 py-4 cursor-pointer flex items-center gap-2 text-lg font-semibold text-yellow-900 hover:bg-yellow-100">
            <AlertCircle className="w-5 h-5" />
            ⚠️ Probleme? Hier finden Sie Lösungen
          </summary>
          <div className="px-6 pb-6 space-y-4">
            {troubleshooting.map((item, idx) => (
              <div key={idx} className="bg-white rounded-lg p-4 border border-yellow-200">
                <h5 className="font-semibold text-yellow-900 mb-2">
                  🔴 {item.problem}
                </h5>
                <p className="text-gray-700">
                  <strong>✅ Lösung:</strong> {item.solution}
                </p>
              </div>
            ))}
          </div>
        </details>
      )}

      {/* Completion Message */}
      {completedSteps.size === steps.length && (
        <div className="bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg p-6 text-white text-center">
          <CheckCircle2 className="w-16 h-16 mx-auto mb-3" />
          <h3 className="text-2xl font-bold mb-2">🎉 Perfekt!</h3>
          <p className="text-green-100">
            Sie haben alle Schritte abgeschlossen. Vergessen Sie nicht, die Lösung zu testen!
          </p>
        </div>
      )}
    </div>
  )
}

