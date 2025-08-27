FROM node:18

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

EXPOSE 3000

# Run the production Next.js server
CMD ["npm", "run", "start"]
