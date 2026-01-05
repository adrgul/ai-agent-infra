# Frontend Setup - Tailwind CSS + Modern UI

## 🎨 Technológia

- **Framework**: Vanilla JavaScript (no build step in development, Tailwind via npm)
- **Styling**: Tailwind CSS 3.3+ (utility-first CSS)
- **Design**: Dark mode, ChatGPT-style UI, gradient headers, smooth animations
- **Server**: Nginx (Alpine) - optimized static file serving

## 📁 Project Structure

```
frontend/
├── package.json              # Node dependencies (tailwindcss)
├── tailwind.config.js        # Tailwind configuration
├── input.css                 # Tailwind directives (@tailwind, @layer)
├── Dockerfile                # Multi-stage Docker build
├── nginx.conf                # Nginx configuration for SPA
├── templates/
│   └── index.html            # Single-page application
└── static/
    └── style.css             # Built Tailwind CSS output (generated)
```

## 🔨 Build Process

### Docker Build (Recommended)
```bash
cd benketibor
docker-compose up --build
```

**Process:**
1. **Builder stage** (Node.js 18-alpine):
   - Install dependencies: `npm install`
   - Build Tailwind CSS: `npm run build`
   - Output: `frontend/static/style.css` (compiled)

2. **Final stage** (Nginx Alpine):
   - Copy compiled CSS to Nginx root
   - Copy templates/static to Nginx serving directory
   - Listen on port 3000

### Local Development (Optional)
```bash
cd frontend
npm install
npm run dev    # Watch mode - rebuilds CSS on changes
```

Then open `index.html` in browser and run local backend separately.

## 🎯 Design Features

### Color Scheme
- **Background**: `#0d0d0d` (near black) with gradient overlay
- **Dark Secondary**: `#1a1a1a`, `#2d2d2d` (for containers)
- **Accent**: `#10a37f` (teal green - ChatGPT-like)
- **Text**: `#ececec` (light gray)
- **Error**: `#d32f2f` (red)
- **Info**: `#1976d2` (blue)

### UI Components
- **Chat Messages**:
  - User: Teal background, right-aligned, rounded corners
  - Bot: Dark gray background, left-aligned, rounded corners
  - Error: Red background, emphasizes issues
  - Info: Blue background, subtle messages

- **Input Area**:
  - Dark background with subtle borders
  - Focus state: Green accent border with glow shadow
  - Smooth transitions on hover/active states

- **Animations**:
  - Slide-in effect for new messages
  - Hover lift effect for buttons
  - Smooth scrolling (scroll-behavior)

- **Accessibility**:
  - Custom scrollbar styling (dark theme)
  - High contrast text for readability
  - Focus states for keyboard navigation

## 📝 Tailwind Configuration

### Key Settings
```javascript
// tailwind.config.js
export default {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        'dark': '#0d0d0d',
        'darker': '#1a1a1a',
        'accent': '#10a37f',
      },
    },
  },
}
```

### Component Layer
```css
@layer components {
  .chat-message { @apply px-4 py-3 rounded-lg max-w-2xl; }
  .user-message { @apply bg-accent text-white ml-auto; }
  .bot-message { @apply bg-gray-700 text-white mr-auto; }
  .btn-primary { @apply bg-accent hover:bg-accent/80 text-white font-semibold py-2 px-4 rounded-lg transition; }
}
```

## 🚀 Deployment

### Docker Build Size Optimization
The multi-stage build keeps final image small:
- Builder: Installs Node + Tailwind, runs build
- Final: Only Nginx + CSS output (drops 400MB+ Node artifacts)

### Static File Caching
Nginx config enables browser caching:
```nginx
location ~* \.(css|js|jpg|jpeg|png|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 🔄 Customization

### Change Theme
Edit `tailwind.config.js`:
```javascript
colors: {
  'accent': '#your-color-here',  // Primary action color
  'dark': '#your-bg-here',       // Background
}
```

### Add New Components
Edit `input.css`:
```css
@layer components {
  .your-component { @apply /* tailwind classes */; }
}
```

Then rebuild:
```bash
npm run build
```

## 📊 Performance

- **CSS Size**: ~15KB (gzipped)
- **Load Time**: <100ms (Nginx optimized)
- **Lighthouse**: Dark mode, optimized images, fast CLS
- **Browser Support**: All modern browsers (ES6+)

## 🐛 Troubleshooting

### CSS Not Loading
1. Check Docker build log: `docker-compose logs frontend`
2. Verify `npm run build` succeeded
3. Check Nginx access logs: `docker exec knowledgerouter_frontend tail -f /var/log/nginx/access.log`

### Styles Not Updating
Run build again:
```bash
docker-compose down -v
docker-compose up --build
```

### Custom Styles Not Working
Make sure they're in `input.css` or inline `<style>` tags in `index.html`.
Tailwind purges unused styles - wrap custom CSS in `@layer` or use `!important` if needed.

---

## 🎫 Jira Ticket Integration (IT Domain)

### Overview
Chat-based Jira ticket creation for IT domain queries. When IT domain provides a response, user can type "igen" to create a Jira ticket.

### Frontend Flow

#### 1. State Management
```javascript
let lastITContext = null;  // Global variable to store IT domain context
```

Stores the context from the last IT response that offered Jira ticket creation.

#### 2. "igen" Detection Logic
```javascript
// queryForm submit handler (around line 331)
const query = queryInput.value.trim();

// Check if this is a Jira ticket confirmation
const isJiraConfirmation = query.toLowerCase() === "igen" || 
                          (query.toLowerCase().includes("igen") && query.length < 10);

if (isJiraConfirmation && lastITContext) {
    await createJiraTicket();
    lastITContext = null;  // Clear context after use
    queryInput.value = "";
    return;  // Don't send as regular query
}
```

**Detection Rules:**
- Exact match: "igen" (case-insensitive)
- Partial match: contains "igen" AND query length < 10 chars
- Context check: `lastITContext` must be set

#### 3. Context Storage
```javascript
// After receiving bot response (around line 447)
if (message.domain === 'it' && message.content.includes('Szeretnéd')) {
    lastITContext = {
        query: message.query,
        response: message.content,
        timestamp: Date.now()
    };
} else if (message.domain !== 'it') {
    lastITContext = null;  // Clear context for non-IT responses
}
```

**Storage Conditions:**
- Domain must be "it"
- Response must contain "Szeretnéd" (Jira offer keyword)
- Context cleared for non-IT responses

#### 4. Ticket Creation Function
```javascript
async function createJiraTicket() {
    if (!lastITContext) {
        addMessage('bot', 'Nincs IT kontextus Jira ticket létrehozásához.', 'error');
        return;
    }

    try {
        const response = await fetch('http://localhost:8001/api/jira/ticket/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                summary: lastITContext.query,
                description: lastITContext.response,
                issue_type: 'Task',
                priority: 'Medium'
            })
        });

        if (!response.ok) throw new Error('Jira API hiba');

        const data = await response.json();
        const ticketLink = `<a href="${data.ticket_url}" target="_blank" style="color:#10a37f;text-decoration:underline;">
                           ${data.ticket_key}
                           </a>`;
        addMessage('bot', `✅ Jira ticket létrehozva: ${ticketLink}`, 'info');
    } catch (error) {
        console.error('Jira ticket error:', error);
        addMessage('bot', '❌ Hiba a Jira ticket létrehozása során.', 'error');
    }
}
```

**API Contract:**
- **Endpoint**: `POST /api/jira/ticket/`
- **Request Body**:
  ```json
  {
    "summary": "VPN problémám van",
    "description": "IT policy alapján a következő lépések...",
    "issue_type": "Task",
    "priority": "Medium"
  }
  ```
- **Response**:
  ```json
  {
    "ticket_key": "SCRUM-123",
    "ticket_url": "https://your-jira.atlassian.net/browse/SCRUM-123"
  }
  ```

### User Experience Flow

1. **IT Query Submitted**:
   ```
   User: "VPN problémám van, mi a teendő?"
   ```

2. **IT Response Received**:
   ```
   Bot: "VPN hibaelhárítási lépések:
         1. Ellenőrizd a csatlakozást...
         2. Próbáld újraindítani...
         
         📋 Szeretnéd, hogy létrehozzak egy Jira ticketet...
         (Válaszolj 'igen'-nel vagy 'nem'-mel)"
   ```
   → `lastITContext` stored

3. **User Confirms**:
   ```
   User: "igen"
   ```
   → Detected as Jira confirmation
   → `createJiraTicket()` called

4. **Ticket Created**:
   ```
   Bot: "✅ Jira ticket létrehozva: SCRUM-123"
   ```
   → Context cleared
   → Link clickable

### Key Changes from Previous Version

#### ❌ Old Approach (UI Buttons)
```javascript
// Removed: handleJiraTicketOffer() function
// Removed: createJiraButtons() function
// Removed: Button click event listeners
```

**Problems:**
- Required separate button handling logic
- Broke conversation flow
- Additional UI complexity

#### ✅ New Approach (Chat-Based)
```javascript
// Simple: "igen" detection + context storage
// Natural: Continues chat conversation
// Clean: No separate button logic
```

**Benefits:**
- More natural conversation flow
- User types response (familiar pattern)
- Simpler codebase
- Consistent with chat UX

### Error Handling

**No Context**:
```javascript
if (!lastITContext) {
    addMessage('bot', 'Nincs IT kontextus...', 'error');
    return;
}
```

**API Error**:
```javascript
if (!response.ok) throw new Error('Jira API hiba');
// Caught and displayed as error message
```

**Network Error**:
```javascript
catch (error) {
    console.error('Jira ticket error:', error);
    addMessage('bot', '❌ Hiba a Jira ticket létrehozása során.', 'error');
}
```

### Configuration

No frontend configuration needed. Jira API endpoint is hardcoded:
```javascript
const response = await fetch('http://localhost:8001/api/jira/ticket/', { ... });
```

Backend handles Jira authentication via environment variables (see IT_DOMAIN_IMPLEMENTATION.md).

### Testing

**Manual Test:**
1. Submit IT query: "Hogyan állítom be a VPN-t?"
2. Wait for response with "Szeretnéd..." text
3. Check `lastITContext` in browser console (should be set)
4. Type "igen"
5. Verify ticket creation message appears
6. Click ticket link → should open Jira

**Debug Logging:**
```javascript
console.log('IT Context stored:', lastITContext);
console.log('Jira confirmation detected:', isJiraConfirmation);
```

---

**Built with ❤️ using Tailwind CSS**
