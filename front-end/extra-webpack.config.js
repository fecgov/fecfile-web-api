const webpack = require('webpack');

// Get environment variables set in node for the build
// const keys = Object.keys(process.env);
// let env = {};
// keys.forEach(key => {
//   if (key === 'ACCESS_KEY' || key === 'SECRET_KEY' || key === 'AWS_SDK_LOAD_CONFIG') {
//     env[key] = JSON.stringify(process.env[key]);
//     // console.log(`${key} is ${env[key]}`);
//   }
// });

// var AWS = require('aws-sdk');

// var credentials = new AWS.SharedIniFileCredentials({ profile: 'default' });
// AWS.config.credentials = credentials;
// console.log('credentials: ', credentials);

// AWS.config.getCredentials(function (err) {
//   if (err) console.log(err.stack);
//   // credentials not loaded
//   else {
//     console.log("Access key from config:", AWS.config.credentials.accessKeyId);
//     console.log("Secret access key from config:", AWS.config.credentials.secretAccessKey);
//     console.log('AWS.config.credentials.constructor:', AWS.config.credentials.constructor);
//   }
// });

module.exports = {
  plugins: [new webpack.DefinePlugin({
    '_process.env': {
      // ACCESS_KEY: JSON.stringify(process.env.ACCESS_KEY),
      // SECRET_KEY: JSON.stringify(process.env.SECRET_KEY)
      // ACCESS_KEY: JSON.stringify(AWS.config.credentials.accessKeyId),
      // SECRET_KEY: JSON.stringify(AWS.config.credentials.secretAccessKey)
      // ACCESS_KEY: JSON.stringify(credentials.accessKeyId),
      // SECRET_KEY: JSON.stringify(credentials.secretAccessKey)
    }
  })]
}
