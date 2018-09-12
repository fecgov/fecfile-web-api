# Stage1 Build the angular artifact
FROM tiangolo/node-frontend:10 as buildArtifact
WORKDIR /app
COPY package*.json /app/
RUN npm install
copy . /app/


RUN npm run build -- --output-path=./dist/out

# Stage2, deploy compiled app to nginx
FROM nginx:1.15
COPY --from=buildArtifact /app/dist/out/ /usr/share/nginx/html
COPY ./nginx/nginx.conf /etc/nginx/conf.d/default.conf
