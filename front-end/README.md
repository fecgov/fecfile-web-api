# FecEFile

This project was generated with [Angular CLI](https://github.com/angular/angular-cli) version 6.0.8.

## Running locally

To run local development environment if Django backend is also running locally at port 8080 run `npm run local`.

## Development server

Run `ng serve` for a dev server. Navigate to `http://localhost:4200/`. The app will automatically reload if you change any of the source files.

## Code scaffolding

Run `ng generate component component-name` to generate a new component. You can also use `ng generate directive|pipe|service|class|guard|interface|enum|module`.

## Build

Run `ng build` to build the project. The build artifacts will be stored in the `dist/` directory. Use the `--prod` flag for a production build.

## Running unit tests

Run `ng test` to execute the unit tests via [Karma](https://karma-runner.github.io).

## Running end-to-end tests

Run `ng e2e` to execute the end-to-end tests via [Protractor](http://www.protractortest.org/).

## Further help

To get more help on the Angular CLI use `ng help` or go check out the [Angular CLI README](https://github.com/angular/angular-cli/blob/master/README.md).

## Mock API

If you need a mock API to begin front end development, you can use the Node server setup within the server directory.
To start the server you run the command `npm run json-server`.


- If on Ubuntu and  Angular CLI stops watching changes suddenly, then increase the notify watches limit on Linux.
  - `sudo sysctl fs.inotify.max_user_watches=524288`
  - `sudo sysctl -p --system`
  - From: https://github.com/angular/angular-cli/issues/2356

