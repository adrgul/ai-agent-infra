FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend code
COPY frontend/ .

# Build Tailwind CSS
RUN npm run build

# Final stage - Nginx
FROM nginx:alpine

# Copy nginx config
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy frontend files to nginx root
COPY frontend/templates /usr/share/nginx/html
COPY frontend/static /usr/share/nginx/html/static

# Copy built CSS from builder
COPY --from=builder /app/static/style.css /usr/share/nginx/html/static/style.css

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
