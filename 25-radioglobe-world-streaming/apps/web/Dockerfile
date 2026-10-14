FROM node:22-alpine AS builder

WORKDIR /app

# Build paytida kerak bo'ladigan ommaviy o'zgaruvchilar.
# NEXT_PUBLIC_* qiymatlari mijoz bundle'iga build vaqtida "pishiriladi",
# shuning uchun ularni runtime'da berish yetarli emas.
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_SITE_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

RUN addgroup -g 10001 nodejs && adduser -u 10001 -G nodejs -S nextjs && chown -R nextjs:nodejs /app
USER nextjs

EXPOSE 3000

CMD ["npm", "start"]
