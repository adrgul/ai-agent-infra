# Multi-stage build for frontend
FROM node:20-alpine AS builder

WORKDIR /build

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build argument for API base URL
ARG VITE_API_BASE=http://localhost:8000
ENV VITE_API_BASE=$VITE_API_BASE

# Build application
RUN npm run build


# Production stage - serve with nginx
FROM nginx:alpine

# Copy built assets from builder
COPY --from=builder /build/dist /usr/share/nginx/html

# Copy nginx config (optional - default works fine)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
