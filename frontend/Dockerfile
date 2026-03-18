FROM node:20-slim

RUN npm install -g pnpm

WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install
COPY . .

CMD ["pnpm", "dev", "--host", "0.0.0.0"]
