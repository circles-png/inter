FROM node:25.2.1 AS builder
ENV CI=true
WORKDIR /usr/src/app
COPY package.json ./
RUN npm i -g pnpm
RUN pnpm i
COPY . .
RUN pnpm run build
RUN pnpm prune --prod

FROM node:25.2.1
WORKDIR /usr/src/app
COPY --from=builder /usr/src/app/build ./build
COPY --from=builder /usr/src/app/node_modules ./node_modules
COPY package.json .
EXPOSE 3000
ENV NODE_ENV=production
CMD ["node", "build"]
