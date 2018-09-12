# Stage1 Build the angular artifact
FROM tiangolo/node-frontend:10 as build-artifact
WORKDIR /app
COPY package*.json /app/
RUN npm install
copy ./ /app/

ARG configuration='production'

RUN npm run build -- --output-path=./dist/out --configuration $configuration

# Stage2, deploy compiled app to nginx
FROM nginx:1.15
COPY --from=build-artifact /app/dist/out/ /usr/share/nginx/html
COPY ./nginx/nginx.conf /etc/nginx/conf.d/default.conf
