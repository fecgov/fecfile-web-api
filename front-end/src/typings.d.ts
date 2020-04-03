/**
 * Define a Process interfaces to include environment variables
 * set in nodeJs server for running local configuration.
 * See environment.local.ts and extra-webpack.config where the _process var is used.
 */
declare var _process: Process;

interface Process {
    env: Env
}

interface Env {
    ACCESS_KEY: string
    SECRET_KEY: string
}

interface GlobalEnvironment {
    process: Process;
}
