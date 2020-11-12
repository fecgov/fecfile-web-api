import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ImportTrxSidebarComponent } from './import-trx-sidebar.component';

describe('ImportTrxSidebarComponent', () => {
  let component: ImportTrxSidebarComponent;
  let fixture: ComponentFixture<ImportTrxSidebarComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ImportTrxSidebarComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ImportTrxSidebarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
