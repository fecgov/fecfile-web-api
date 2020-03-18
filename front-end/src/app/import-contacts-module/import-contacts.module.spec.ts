import { ImportContactsModule } from './import-contacts.module';

describe('ImportContactsModule', () => {
  let importContactsModule: ImportContactsModule;

  beforeEach(() => {
    importContactsModule = new ImportContactsModule();
  });

  it('should create an instance', () => {
    expect(importContactsModule).toBeTruthy();
  });
});
