FROM node:18-alpine

WORKDIR /app

# Package files kopieren
COPY package*.json ./

# Dependencies installieren
RUN npm install --only=production

# Source code kopieren
COPY . .

# Port exponieren
EXPOSE 3000

# Production build und start
RUN npm run build
CMD ["npm", "start"]
