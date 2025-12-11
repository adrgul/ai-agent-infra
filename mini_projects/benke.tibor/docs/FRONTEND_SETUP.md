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

**Built with ❤️ using Tailwind CSS**
