'use client'

import { useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Check, Copy } from 'lucide-react'

interface CodeSnippetWithCopyProps {
  code: string
  language?: string
  filename?: string
}

export function CodeSnippetWithCopy({ 
  code, 
  language = 'html',
  filename 
}: CodeSnippetWithCopyProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Failed to copy:', error)
    }
  }

  return (
    <div className="relative group rounded-lg overflow-hidden bg-gray-900 border border-gray-700">
      {/* Header mit Filename und Copy-Button */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
        {filename && (
          <span className="text-xs text-gray-400 font-mono">{filename}</span>
        )}
        <button
          onClick={handleCopy}
          className={`
            ml-auto flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium
            transition-all duration-200
            ${copied 
              ? 'bg-green-600 text-white' 
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }
          `}
          aria-label={copied ? 'Kopiert!' : 'Code kopieren'}
        >
          {copied ? (
            <>
              <Check className="w-4 h-4" />
              <span>Kopiert!</span>
            </>
          ) : (
            <>
              <Copy className="w-4 h-4" />
              <span>Kopieren</span>
            </>
          )}
        </button>
      </div>

      {/* Code Block */}
      <div className="overflow-x-auto">
        <SyntaxHighlighter
          language={language}
          style={vscDarkPlus}
          customStyle={{
            margin: 0,
            padding: '1rem',
            fontSize: '0.875rem',
            lineHeight: '1.5',
            background: 'transparent'
          }}
          showLineNumbers
          wrapLines
        >
          {code}
        </SyntaxHighlighter>
      </div>
    </div>
  )
}

