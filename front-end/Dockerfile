# base image
FROM node:10 as builder

RUN mkdir /usr/src/app
WORKDIR /usr/src/app

# add `/usr/src/app/node_modules/.bin` to $PATH
ENV PATH /usr/src/app/node_modules/.bin:$PATH
# RUN npm install -g npm to update

# install and cache app dependencies
COPY package.json /usr/src/app/package.json
RUN npm install
RUN npm install -g @angular/cli

# add app
COPY . /usr/src/app

RUN node --max-old-space-size=4096 /usr/src/app/node_modules/.bin/ng build --aot --source-map --configuration=local

# start app
#CMD ng serve --host 0.0.0.0

FROM nginx:latest

ARG gitTag=VERDEPLOYED

# Copy local nginx config file
COPY ./nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Copy artifact to nginx default html dir
COPY --from=builder /usr/src/app/dist/fec-eFilling /usr/share/nginx/html

RUN mv /etc/localtime /etc/localtime.backup && ln -s /usr/share/zoneinfo/EST5EDT /etc/localtime

# Add a tag at the bottom of index.html if deployed to dev or qa 
RUN sh -c ' d=`TZ=America/New_York date`; echo "<!-- ${d} --><!-- ${gitTag} -->" >> /usr/share/nginx/html/index.html '


EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
