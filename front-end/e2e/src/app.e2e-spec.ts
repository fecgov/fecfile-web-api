import { AppPage } from './app.po';

describe('workspace-project App', () => {
  let page: AppPage;

  beforeEach(() => {
    page = new AppPage();
  });

  xit('should display welcome message', async () => {
    await page.navigateTo();

    expect(page.getParagraphText()).toEqual('FEC File Online');
  });
});
