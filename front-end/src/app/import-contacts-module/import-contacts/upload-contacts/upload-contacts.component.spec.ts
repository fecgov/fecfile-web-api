import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { UploadContactsComponent } from './upload-contacts.component';

describe('UploadContactsComponent', () => {
  let component: UploadContactsComponent;
  let fixture: ComponentFixture<UploadContactsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ UploadContactsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(UploadContactsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
