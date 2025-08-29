# 🎨 Complyo Design System
## Professional UI/UX Guidelines for Enterprise Compliance Platform

---

## 🎯 **DESIGN PHILOSOPHY**

### **Core Values**:
- **Trust & Security**: Visual elements that convey reliability and protection
- **Simplicity**: Complex compliance made simple and approachable  
- **Professionalism**: Enterprise-grade appearance for B2B credibility
- **Accessibility**: Inclusive design for all users and skill levels
- **Clarity**: Clear information hierarchy and intuitive navigation

### **Target Audience Psychology**:
- **Primary**: Non-tech business owners (anxious about compliance)
- **Secondary**: Marketing managers (need quick wins)
- **Tertiary**: Developers (want technical depth)

---

## 🎨 **VISUAL IDENTITY**

### **Brand Colors**:

#### **Primary Palette**:
```css
/* Primary Blue - Trust & Security */
--complyo-blue-900: #0F172A    /* Dark headings */
--complyo-blue-800: #1E293B    /* Body text */
--complyo-blue-700: #334155    /* Secondary text */
--complyo-blue-600: #475569    /* Muted text */
--complyo-blue-500: #64748B    /* Borders */

/* Accent Blue - CTAs & Links */
--complyo-accent-600: #2563EB  /* Primary CTA */
--complyo-accent-500: #3B82F6  /* Hover states */
--complyo-accent-400: #60A5FA  /* Light accents */
--complyo-accent-100: #DBEAFE  /* Background tints */
```

#### **Status Colors**:
```css
/* Success - Green */
--complyo-success-600: #059669  /* Success states */
--complyo-success-500: #10B981  /* Success buttons */
--complyo-success-100: #D1FAE5  /* Success backgrounds */

/* Warning - Amber */
--complyo-warning-600: #D97706  /* Warning states */
--complyo-warning-500: #F59E0B  /* Warning buttons */
--complyo-warning-100: #FEF3C7  /* Warning backgrounds */

/* Error - Red */
--complyo-error-600: #DC2626   /* Error states */
--complyo-error-500: #EF4444   /* Error buttons */
--complyo-error-100: #FEE2E2   /* Error backgrounds */

/* Info - Cyan */
--complyo-info-600: #0891B2    /* Info states */
--complyo-info-500: #06B6D4    /* Info buttons */
--complyo-info-100: #CFFAFE    /* Info backgrounds */
```

#### **Neutral Palette**:
```css
/* Grays */
--complyo-gray-900: #111827    /* Darkest text */
--complyo-gray-800: #1F2937    /* Dark text */
--complyo-gray-700: #374151    /* Medium text */
--complyo-gray-600: #4B5563    /* Light text */
--complyo-gray-500: #6B7280    /* Muted text */
--complyo-gray-400: #9CA3AF    /* Placeholder text */
--complyo-gray-300: #D1D5DB    /* Light borders */
--complyo-gray-200: #E5E7EB    /* Dividers */
--complyo-gray-100: #F3F4F6    /* Light backgrounds */
--complyo-gray-50: #F9FAFB     /* Page backgrounds */
--complyo-white: #FFFFFF       /* Pure white */
```

### **Typography**:

#### **Font Stack**:
```css
/* Primary Font - Inter (Modern, Professional) */
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

/* Monospace Font - JetBrains Mono (Code blocks) */
--font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;

/* Display Font - Cal Sans (Headlines) */
--font-display: 'Cal Sans', 'Inter', sans-serif;
```

#### **Type Scale**:
```css
/* Font Sizes */
--text-xs: 0.75rem;    /* 12px - Captions */
--text-sm: 0.875rem;   /* 14px - Body small */
--text-base: 1rem;     /* 16px - Body */
--text-lg: 1.125rem;   /* 18px - Body large */
--text-xl: 1.25rem;    /* 20px - H5 */
--text-2xl: 1.5rem;    /* 24px - H4 */
--text-3xl: 1.875rem;  /* 30px - H3 */
--text-4xl: 2.25rem;   /* 36px - H2 */
--text-5xl: 3rem;      /* 48px - H1 */
--text-6xl: 3.75rem;   /* 60px - Hero */
--text-7xl: 4.5rem;    /* 72px - Display */

/* Font Weights */
--font-light: 300;
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
--font-extrabold: 800;
```

#### **Typography Usage**:
- **Headlines**: Cal Sans, Bold, Dark Blue
- **Body Text**: Inter, Regular, Gray-800
- **CTAs**: Inter, Semibold, White on Blue
- **Captions**: Inter, Medium, Gray-600
- **Code**: JetBrains Mono, Regular, Gray-700

---

## 🔲 **LAYOUT & SPACING**

### **Grid System**:
```css
/* Container Sizes */
--container-sm: 640px;    /* Mobile */
--container-md: 768px;    /* Tablet */
--container-lg: 1024px;   /* Desktop */
--container-xl: 1280px;   /* Large Desktop */
--container-2xl: 1536px;  /* Extra Large */

/* Spacing Scale (Tailwind-based) */
--space-px: 1px;
--space-0: 0rem;
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
--space-20: 5rem;     /* 80px */
--space-24: 6rem;     /* 96px */
```

### **Layout Principles**:
- **8px Grid**: All spacing based on 8px increments
- **Golden Ratio**: 1.618 for section proportions
- **Breathing Room**: Generous whitespace for clarity
- **Hierarchy**: Clear visual hierarchy through spacing

---

## 🎭 **COMPONENT LIBRARY**

### **Buttons**:

#### **Primary Button (CTA)**:
```css
.btn-primary {
  background: var(--complyo-accent-600);
  color: var(--complyo-white);
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 600;
  font-size: 1rem;
  transition: all 0.2s;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.btn-primary:hover {
  background: var(--complyo-accent-700);
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
```

#### **Secondary Button**:
```css
.btn-secondary {
  background: transparent;
  color: var(--complyo-accent-600);
  border: 1px solid var(--complyo-accent-600);
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 600;
}
```

#### **Danger Button**:
```css
.btn-danger {
  background: var(--complyo-error-600);
  color: var(--complyo-white);
  /* ... rest similar to primary */
}
```

### **Cards**:
```css
.card {
  background: var(--complyo-white);
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--complyo-gray-200);
  padding: 1.5rem;
  transition: all 0.2s;
}

.card:hover {
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}
```

### **Forms**:
```css
.form-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid var(--complyo-gray-300);
  border-radius: 0.5rem;
  font-size: 1rem;
  transition: all 0.2s;
}

.form-input:focus {
  border-color: var(--complyo-accent-500);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
  outline: none;
}
```

---

## 🎯 **DASHBOARD UI SPECIFICATIONS**

### **Navigation Structure**:
```
🏠 Dashboard Home
├── 📊 Overview (Compliance Score, Quick Stats)
├── 🔍 Website Scanner (Start New Scan)
├── 📋 Journey Progress (Current Workflow Step)
├── 📜 Reports & Certificates
├── ⚙️ Settings & Profile
└── 💳 Subscription & Billing
```

### **Dashboard Layout**:

#### **Header (Fixed)**:
- **Logo**: Complyo wordmark (left)
- **Navigation**: Horizontal tabs (center)
- **User Menu**: Avatar + dropdown (right)
- **Height**: 64px
- **Background**: White with subtle border

#### **Sidebar (Optional)**:
- **Width**: 256px (desktop), collapsible
- **Background**: Gray-50
- **Navigation**: Vertical with icons
- **User Context**: Current plan, usage

#### **Main Content Area**:
- **Max Width**: 1200px
- **Padding**: 24px
- **Background**: Gray-50
- **Cards**: White background with shadows

### **Dashboard Components**:

#### **Compliance Score Widget**:
```
┌─────────────────────────────────┐
│  🛡️ Compliance Score            │
│                                 │
│         85%                     │
│    ████████░░                   │
│                                 │
│  ✅ GDPR: Compliant            │
│  ⚠️ TTDSG: 3 Issues            │
│  ✅ Accessibility: Good        │
└─────────────────────────────────┘
```

#### **Quick Actions Panel**:
```
┌─────────────────────────────────┐
│  Quick Actions                  │
│                                 │
│  [🔍 Scan Website]             │
│  [📋 View Report]              │
│  [🚀 Start Journey]            │
│  [💳 Upgrade Plan]             │
└─────────────────────────────────┘
```

#### **Journey Progress**:
```
┌─────────────────────────────────┐
│  📋 Current Journey             │
│                                 │
│  Step 3 of 13: Website Setup   │
│  ████████░░░░░░░░░░ 60%        │
│                                 │
│  Next: Configure Cookie Banner │
│  [Continue Journey →]          │
└─────────────────────────────────┘
```

---

## 📱 **RESPONSIVE DESIGN**

### **Breakpoints**:
- **Mobile**: 320px - 767px (Single column)
- **Tablet**: 768px - 1023px (Adjusted layout)
- **Desktop**: 1024px - 1439px (Full layout)
- **Large**: 1440px+ (Max width container)

### **Mobile-First Approach**:
- Start with mobile design
- Progressive enhancement for larger screens
- Touch-friendly interactions (44px minimum)
- Readable text sizes (16px minimum)

---

## 🎨 **VISUAL ELEMENTS**

### **Icons**:
- **Style**: Lucide React (outline style)
- **Size**: 16px, 20px, 24px standard
- **Color**: Inherits text color
- **Usage**: Consistent meanings across platform

### **Illustrations**:
- **Style**: Minimal, geometric
- **Colors**: Brand palette only
- **Usage**: Empty states, onboarding, errors
- **Format**: SVG for scalability

### **Photography**:
- **Style**: Professional, diverse, authentic
- **Treatment**: Subtle color overlay with brand colors
- **Usage**: Team photos, testimonials, case studies

### **Shadows & Depth**:
```css
/* Shadow Scale */
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.1);
--shadow-2xl: 0 25px 50px rgba(0, 0, 0, 0.25);
```

---

## ♿ **ACCESSIBILITY GUIDELINES**

### **WCAG 2.1 AA Compliance**:
- **Color Contrast**: Minimum 4.5:1 for normal text
- **Color Independence**: Information not conveyed by color alone
- **Keyboard Navigation**: All interactive elements accessible
- **Screen Readers**: Proper ARIA labels and semantic HTML
- **Focus Indicators**: Clear focus states for all controls

### **Inclusive Design**:
- **Font Size**: Minimum 16px, scalable to 200%
- **Touch Targets**: Minimum 44px for mobile
- **Motion**: Respect prefers-reduced-motion
- **Language**: Clear, simple language (8th grade reading level)

---

## 🎭 **MICRO-INTERACTIONS**

### **Animation Principles**:
- **Duration**: 200-300ms for UI feedback
- **Easing**: Ease-out for entrances, ease-in for exits
- **Purpose**: Provide feedback, guide attention, show relationships

### **Common Animations**:
- **Button Hover**: Slight lift + shadow increase
- **Card Hover**: Subtle lift + shadow
- **Loading States**: Skeleton screens, spinners
- **Page Transitions**: Slide or fade
- **Form Validation**: Shake for errors, checkmark for success

---

## 📏 **DESIGN TOKENS (CSS Custom Properties)**

### **Complete Token Set**:
```css
:root {
  /* Colors */
  --color-primary-50: #eff6ff;
  --color-primary-100: #dbeafe;
  --color-primary-500: #3b82f6;
  --color-primary-600: #2563eb;
  --color-primary-900: #1e3a8a;
  
  /* Typography */
  --font-family-sans: 'Inter', system-ui, sans-serif;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  
  /* Spacing */
  --spacing-xs: 0.5rem;
  --spacing-sm: 0.75rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  
  /* Border Radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  
  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-base: 200ms ease;
  --transition-slow: 300ms ease;
}
```

---

## 🎨 **BRAND VOICE & MESSAGING**

### **Tone of Voice**:
- **Professional** but not intimidating
- **Confident** but not arrogant  
- **Helpful** but not condescending
- **Clear** but not oversimplified

### **Key Messages**:
- **"Compliance made simple"** - Main value proposition
- **"From chaos to compliance in minutes"** - Speed benefit
- **"Your legal safety net"** - Security benefit
- **"Built by experts, designed for everyone"** - Trust + accessibility

---

This design system ensures consistency across all Complyo touchpoints while maintaining professional credibility and user-friendly accessibility.