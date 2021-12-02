export const environment = {
  production: false,
  name: 'local',
  apiUrl: 'http://localhost/api/v1',
  appTitle: 'FECfile',
  validateSuccess: 'All required fields have passed validation.',
  awsRegion: 'us-east-1',
  awsIdentityPoolId: 'us-east-1:f0f414b2-8e9f-4488-9cc1-34a5918a1a1d',
  ACCESS_KEY: "_process.env.ACCESS_KEY", //TODO: fix this. Hacked to get Angular 8 upgrade working
  SECRET_KEY: "_process.env.SECRET_KEY", //TODO: fix this. Hacked to get Angular 8 upgrade working
  dcfConverterApiUrl: 'https://dev-efile-api.efdev.fec.gov/dcf_converter/v1'
};
