# Build frontend
FROM node:20-alpine AS build
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json* /src/frontend/
WORKDIR /src/frontend
RUN npm install
COPY frontend /src/frontend
RUN npm run build

# Nginx to serve frontend + proxy /api
FROM nginx:1.27-alpine
COPY web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/frontend/dist /usr/share/nginx/html
EXPOSE 80
