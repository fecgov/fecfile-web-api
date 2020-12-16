import { ImportFecfileModuleModule } from './import-fecfile.module';

describe('ImportFecfileModuleModule', () => {
  let importFecfileModuleModule: ImportFecfileModuleModule;

  beforeEach(() => {
    importFecfileModuleModule = new ImportFecfileModuleModule();
  });

  it('should create an instance', () => {
    expect(importFecfileModuleModule).toBeTruthy();
  });
});
