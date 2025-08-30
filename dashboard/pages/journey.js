/**
 * Complyo Journey Page - User Workflow Interface
 * Complete guided experience from registration to compliance
 */

import React from 'react';
import Head from 'next/head';
import WorkflowJourney from '../components/WorkflowJourney';

export default function JourneyPage() {
  return (
    <>
      <Head>
        <title>Compliance Journey - Complyo</title>
        <meta name="description" content="Ihre persönliche Reise zur 100% rechtssicheren Website mit Complyo" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-2xl font-bold text-blue-600">Complyo</h1>
                <span className="ml-2 text-sm text-gray-500">Journey</span>
              </div>
              <div className="flex items-center space-x-4">
                <a 
                  href="/dashboard" 
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Dashboard
                </a>
                <a 
                  href="/support" 
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Support
                </a>
                <button 
                  onClick={() => {
                    localStorage.removeItem('token');
                    sessionStorage.removeItem('auth_token');
                    window.location.href = '/';
                  }}
                  className="bg-red-100 text-red-700 hover:bg-red-200 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Journey Component */}
        <main className="py-8">
          <WorkflowJourney />
        </main>

        {/* Footer */}
        <footer className="bg-white border-t mt-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="text-center text-gray-600">
              <p>&copy; 2024 Complyo. Ihre Website rechtssicher machen - einfach und automatisiert.</p>
              <div className="mt-2 space-x-4 text-sm">
                <a href="/privacy" className="hover:text-gray-900">Datenschutz</a>
                <a href="/terms" className="hover:text-gray-900">AGB</a>
                <a href="/imprint" className="hover:text-gray-900">Impressum</a>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}

// This function gets called at build time on server-side
// It will pre-render this page on build time using the props returned by getStaticProps
export async function getStaticProps() {
  return {
    props: {
      title: 'Compliance Journey',
      description: 'Ihre persönliche Reise zur 100% rechtssicheren Website'
    },
  }
}