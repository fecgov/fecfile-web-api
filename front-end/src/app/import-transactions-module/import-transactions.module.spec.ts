import { ImportTransactionsModule } from './import-transactions.module';

describe('ImportTransactionsModule', () => {
  let importTransactionsModule: ImportTransactionsModule;

  beforeEach(() => {
    importTransactionsModule = new ImportTransactionsModule();
  });

  it('should create an instance', () => {
    expect(importTransactionsModule).toBeTruthy();
  });
});
