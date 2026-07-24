# syntax=docker/dockerfile:1.7
FROM node:20.20.2-alpine AS build

WORKDIR /app
ARG VITE_API_BASE_URL=http://localhost:8000/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci \
      --prefer-offline \
      --no-audit \
      --no-fund \
      --maxsockets=1 \
      --fetch-retries=5 \
      --fetch-retry-mintimeout=1000 \
      --fetch-retry-maxtimeout=30000 \
      --fetch-timeout=300000

COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://127.0.0.1/health || exit 1
