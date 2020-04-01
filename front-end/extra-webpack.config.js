const webpack = require('webpack');

const keys = Object.keys(process.env);
let env = {};
keys.forEach(key => {
  if (key === 'ACCESS_KEY' || key === 'SECRET_KEY') {
    env[key] = JSON.stringify(process.env[key]);
    console.log(`${key} is ${env[key]}`);
  }
});

module.exports = {
  plugins: [new webpack.DefinePlugin({
    '_process.env': {
      ACCESS_KEY: JSON.stringify(process.env.ACCESS_KEY),
      SECRET_KEY: JSON.stringify(process.env.SECRET_KEY)
    }
  })]
}
