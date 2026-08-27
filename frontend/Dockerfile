# Shared base with dependencies installed.
FROM node:20-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci

# --- dev: hot-reload server, used by docker-compose (target: dev) ---
FROM base AS dev
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# --- build: produce the optimized production build ---
FROM base AS build
COPY . .
RUN npm run build

# --- prod: default target, runs the built app ---
FROM node:20-alpine AS prod
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/package*.json ./
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/.next ./.next
COPY --from=build /app/next.config.js ./next.config.js
EXPOSE 3000
CMD ["npm", "run", "start"]
