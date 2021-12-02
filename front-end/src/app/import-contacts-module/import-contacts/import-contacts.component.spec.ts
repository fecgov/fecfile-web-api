import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ImportContactsComponent } from './import-contacts.component';

describe('ImportContactsComponent', () => {
  let component: ImportContactsComponent;
  let fixture: ComponentFixture<ImportContactsComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ImportContactsComponent]
    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ImportContactsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
