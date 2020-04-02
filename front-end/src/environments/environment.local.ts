export const environment = {
  production: false,
  name: 'local',
  apiUrl: 'http://localhost:8080/api/v1',
  appTitle: 'FECfile',
  validateSuccess: 'All required fields have passed validation.',
  ACCESS_KEY: _process.env.ACCESS_KEY,
  SECRET_KEY: _process.env.SECRET_KEY
};
