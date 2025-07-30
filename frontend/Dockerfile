# Frontend Dockerfile
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json yarn.lock ./

# Install dependencies
RUN yarn install --frozen-lockfile

# Copy the application code
COPY . .

# Build the application
RUN yarn build

# Expose the port
EXPOSE 3000

# Command to run the application
CMD ["yarn", "start"]