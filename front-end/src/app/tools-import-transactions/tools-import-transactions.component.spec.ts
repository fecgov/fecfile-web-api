import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ToolsImportTransactionsComponent } from './tools-import-transactions.component';

describe('ToolsImportTransactionsComponent', () => {
  let component: ToolsImportTransactionsComponent;
  let fixture: ComponentFixture<ToolsImportTransactionsComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ ToolsImportTransactionsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ToolsImportTransactionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
