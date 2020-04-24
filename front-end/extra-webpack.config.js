const webpack = require('webpack');

module.exports = {
  plugins: [new webpack.DefinePlugin({
    '_process.env': {
      // Hard Coded example of env var
      // EXAMPLE_VAR1: 'some-value',
      // Example of variable taken from node at build time
      // For example:
      //   export EXAMPLE_VAR2=some-value
      //   run `EXAMPLE_VAR2=$EXAMPLE_VAR2 npm run local`
      // EXAMPLE_VAR2: JSON.stringify(process.env.EXAMPLE_VAR2),
    }
  })]
}
