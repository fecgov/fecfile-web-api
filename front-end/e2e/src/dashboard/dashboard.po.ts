import { browser, by, element } from 'protractor';

export class DashboardPage {
  getParagraphText() {
    return element(by.css('app-root h1'));
  }
}
