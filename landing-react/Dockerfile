FROM node:18-alpine
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Environment variables
ENV NODE_ENV=development

EXPOSE 3000

# Start in development mode
CMD ["npm", "run", "dev", "--", "--port", "3000", "--hostname", "0.0.0.0"]
