# base image
FROM node:9.6.1 as builder

RUN mkdir /usr/src/app
WORKDIR /usr/src/app

# add `/usr/src/app/node_modules/.bin` to $PATH
ENV PATH /usr/src/app/node_modules/.bin:$PATH

# install and cache app dependencies
COPY package.json /usr/src/app/package.json
RUN npm install
RUN npm install -g @angular/cli

# add app
COPY . /usr/src/app

RUN ng build --configuration=awsdev

# start app
#CMD ng serve --host 0.0.0.0

FROM nginx:latest

# Copy local nginx config file 
COPY ./nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Copy artifact to nginx default html dir
COPY --from=builder /usr/src/app/dist/fec-eFilling /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
