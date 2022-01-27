import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ImportDoneContactsComponent } from './import-done-contacts.component';

describe('ImportDoneContactsComponent', () => {
  let component: ImportDoneContactsComponent;
  let fixture: ComponentFixture<ImportDoneContactsComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ ImportDoneContactsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ImportDoneContactsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
