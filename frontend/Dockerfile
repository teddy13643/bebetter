FROM node:20-slim

WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .

CMD ["npx", "next", "dev", "--port", "3000", "--hostname", "0.0.0.0"]
