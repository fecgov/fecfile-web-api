import { browser, by, element } from 'protractor';

export class DashboardPage {
  getParagraphText() {
    return element(by.css('app-root h1'));
  }

  getNavbar() {
    return element(by.xpath("//nav[contains(@class,'navbar')]"))
  }
}
