export const environment = {
  production: false,
  name: 'local',
  apiUrl: 'http://localhost:8080/api/v1',
  appTitle: 'FECfile',
  validateSuccess: 'All required fields have passed validation.',
  awsRegion: 'us-east-1',
  awsIdentityPoolId: 'us-east-1:f0f414b2-8e9f-4488-9cc1-34a5918a1a1d',
  ACCESS_KEY: _process.env.ACCESS_KEY,
  SECRET_KEY: _process.env.SECRET_KEY
};
