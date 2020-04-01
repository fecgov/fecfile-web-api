export const environment = {
  production: true,
  name: 'awsdev',
  apiUrl: 'https://dev-fecfile-api.efdev.fec.gov/api/v1',
  validateSuccess: 'All required fields have passed validation.',
  appTitle: 'FECfile',
  ACCESS_KEY: _process.env.ACCESS_KEY,
  SECRET_KEY: _process.env.SECRET_KEY
};
