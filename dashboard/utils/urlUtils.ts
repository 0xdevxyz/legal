// 🔧 COMPLYO URL NORMALIZATION FIX
// File: /opt/projects/saas-project-2/dashboard/utils/urlUtils.ts

/**
 * Enhanced URL normalization that fixes the 422 errors
 * Based on diagnostic results showing backend requires protocol
 */

export interface URLValidationResult {
  isValid: boolean;
  normalizedUrl?: string;
  error?: string;
}

/**
 * Normalize URL to ensure backend compatibility
 * Fixes: 422 errors for URLs without protocol
 */
export function normalizeUrl(input: string): string {
  if (!input || typeof input !== 'string') {
    throw new Error('URL is required and must be a string');
  }

  let url = input.trim();
  
  if (!url) {
    throw new Error('URL cannot be empty');
  }

  // Remove common user input issues
  url = url.replace(/^www\./, ''); // Remove leading www
  url = url.replace(/\/$/, ''); // Remove trailing slash
  
  // Add https:// if no protocol is present
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    url = 'https://' + url;
  }

  // Validate the final URL
  try {
    const urlObj = new URL(url);
    
    // Basic domain validation
    if (!urlObj.hostname || urlObj.hostname.length < 3) {
      throw new Error('Invalid domain');
    }
    
    if (!urlObj.hostname.includes('.')) {
      throw new Error('Domain must contain at least one dot');
    }
    
    return url;
  } catch (error) {
    throw new Error(`Invalid URL format: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Validate URL without throwing errors
 * Useful for form validation feedback
 */
export function validateUrl(input: string): URLValidationResult {
  try {
    const normalizedUrl = normalizeUrl(input);
    return {
      isValid: true,
      normalizedUrl
    };
  } catch (error) {
    return {
      isValid: false,
      error: error instanceof Error ? error.message : 'Invalid URL'
    };
  }
}

/**
 * Enhanced API call with proper URL normalization
 * This replaces your current analyze function
 */
export async function analyzeWebsite(url: string): Promise<any> {
  try {
    // Step 1: Normalize URL (this fixes the 422 errors)
    const normalizedUrl = normalizeUrl(url);
    console.log(`🔧 URL normalized: "${url}" → "${normalizedUrl}"`);
    
    // Step 2: Make API request with normalized URL
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ url: normalizedUrl }),
      credentials: 'include'
    });

    console.log(`📡 API Response: ${response.status} ${response.statusText}`);

    // Step 3: Handle response
    if (!response.ok) {
      let errorMessage = `API Error: ${response.status} ${response.statusText}`;
      
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = Array.isArray(errorData.detail) 
            ? errorData.detail.map((err: any) => err.msg || err.message || JSON.stringify(err)).join(', ')
            : errorData.detail;
        }
      } catch (parseError) {
        console.warn('Could not parse error response:', parseError);
        errorMessage = `Server returned ${response.status}: ${response.statusText}`;
      }
      
      throw new Error(errorMessage);
    }

    const data = await response.json();
    console.log('✅ Analysis successful:', data);
    
    return data;

  } catch (error) {
    console.error('❌ Analysis failed:', error);
    
    // Re-throw with user-friendly message
    if (error instanceof Error) {
      throw error;
    } else {
      throw new Error('Analysis failed. Please try again.');
    }
  }
}

/**
 * Test function to verify URL normalization
 * Run this in browser console to test
 */
export function testUrlNormalization(): void {
  const testCases = [
    'github.com',                    // Should add https://
    'www.github.com',               // Should remove www and add https://
    'http://github.com',            // Should keep as-is
    'https://github.com',           // Should keep as-is
    'https://github.com/',          // Should remove trailing slash
    'panoart360.de',               // Should add https://
    'invalid-url',                 // Should throw error
    '',                            // Should throw error
  ];

  console.log('🧪 URL Normalization Test Results:');
  console.log('='.repeat(50));

  testCases.forEach(testUrl => {
    try {
      const result = normalizeUrl(testUrl);
      console.log(`✅ "${testUrl}" → "${result}"`);
    } catch (error) {
      console.log(`❌ "${testUrl}" → ${error instanceof Error ? error.message : 'Error'}`);
    }
  });

  console.log('='.repeat(50));
}

// React Hook for URL validation in forms
import { useState, useCallback } from 'react';

export function useUrlValidation() {
  const [urlError, setUrlError] = useState<string>('');
  const [isValidating, setIsValidating] = useState(false);

  const validateUrlInput = useCallback((input: string): boolean => {
    setIsValidating(true);
    
    try {
      if (!input.trim()) {
        setUrlError('');
        setIsValidating(false);
        return false;
      }

      normalizeUrl(input);
      setUrlError('');
      setIsValidating(false);
      return true;
    } catch (error) {
      setUrlError(error instanceof Error ? error.message : 'Invalid URL');
      setIsValidating(false);
      return false;
    }
  }, []);

  const clearError = useCallback(() => {
    setUrlError('');
  }, []);

  return {
    urlError,
    isValidating,
    validateUrlInput,
    clearError
  };
}
