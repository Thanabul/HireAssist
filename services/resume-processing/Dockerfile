FROM node:22-alpine

WORKDIR /app

# Install production dependencies first so this layer is cached
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY server.js openapi.yaml ./

ENV PORT=3000
EXPOSE 3000

# Run as the unprivileged user that ships with the node image
USER node

CMD ["node", "server.js"]
