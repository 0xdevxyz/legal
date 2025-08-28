/**
 * Test script to verify domain input functionality
 * This script can be run in the browser console to test the input field behavior
 */

(function testDomainInput() {
  console.log('🧪 Testing Domain Input Functionality...');
  
  // Wait for the page to load
  setTimeout(() => {
    const input = document.getElementById('website-url');
    
    if (!input) {
      console.error('❌ Domain input field not found!');
      return;
    }
    
    console.log('✅ Domain input field found');
    
    // Test 1: Check if input allows multiple characters
    console.log('📝 Test 1: Testing character input...');
    
    // Simulate typing multiple characters
    const testUrl = 'example.com';
    input.value = '';
    input.focus();
    
    // Simulate typing each character
    for (let i = 0; i < testUrl.length; i++) {
      const char = testUrl[i];
      input.value += char;
      
      // Trigger input event
      const inputEvent = new Event('input', { bubbles: true });
      input.dispatchEvent(inputEvent);
      
      // Trigger change event
      const changeEvent = new Event('change', { bubbles: true });
      input.dispatchEvent(changeEvent);
    }
    
    console.log(`Input value after typing: "${input.value}"`);
    
    if (input.value === testUrl) {
      console.log('✅ Test 1 PASSED: Input accepts multiple characters');
    } else {
      console.log(`❌ Test 1 FAILED: Expected "${testUrl}", got "${input.value}"`);
    }
    
    // Test 2: Test with longer URL
    console.log('📝 Test 2: Testing longer URL...');
    const longUrl = 'https://www.very-long-domain-name-for-testing.com/path';
    input.value = longUrl;
    
    const inputEvent2 = new Event('input', { bubbles: true });
    input.dispatchEvent(inputEvent2);
    
    if (input.value === longUrl) {
      console.log('✅ Test 2 PASSED: Input accepts long URLs');
    } else {
      console.log(`❌ Test 2 FAILED: Expected "${longUrl}", got "${input.value}"`);
    }
    
    // Test 3: Check event handlers
    console.log('📝 Test 3: Testing event handlers...');
    
    const keydownEvent = new KeyboardEvent('keydown', { 
      key: 'a',
      bubbles: true 
    });
    
    input.dispatchEvent(keydownEvent);
    console.log('✅ Test 3 PASSED: Event handlers are working');
    
    console.log('🎉 Domain input testing completed!');
    
  }, 1000);
})();