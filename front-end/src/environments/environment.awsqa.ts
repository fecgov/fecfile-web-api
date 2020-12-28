export const environment = {
  production: true,
  name: 'awsuat',
  apiUrl: 'https://qa-fecfile-api.efdev.fec.gov/api/v1',
  validateSuccess: 'All required fields have passed validation',
  appTitle: 'FECfile',
  awsRegion: 'us-east-1',
  awsIdentityPoolId: 'us-east-1:f0f414b2-8e9f-4488-9cc1-34a5918a1a1d',
  ACCESS_KEY: _process.env.ACCESS_KEY,
  SECRET_KEY: _process.env.SECRET_KEY,
  dcfConverterApiUrl: 'https://qa-efile-api.efdev.fec.gov/dcf_converter/v1'
};
