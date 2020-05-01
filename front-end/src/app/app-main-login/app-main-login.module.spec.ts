import { AppMainLoginModule } from './app-main-login.module';

describe('AppMainLoginModule', () => {
  let appMainLoginModule: AppMainLoginModule;

  beforeEach(() => {
    appMainLoginModule = new AppMainLoginModule();
  });

  it('should create an instance', () => {
    expect(appMainLoginModule).toBeTruthy();
  });
});
