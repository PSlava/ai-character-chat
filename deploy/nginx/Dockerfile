# Stage 1: Build frontend
FROM node:20-alpine AS build

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

ARG NGINX_CONF=nginx-ssl.conf

# Remove default config and add ours
RUN rm /etc/nginx/conf.d/default.conf
COPY deploy/nginx/${NGINX_CONF} /etc/nginx/conf.d/default.conf

# Copy built frontend
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80 443
