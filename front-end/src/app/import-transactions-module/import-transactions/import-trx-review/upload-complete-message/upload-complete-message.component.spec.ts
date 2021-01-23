import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { UploadCompleteMessageComponent } from './upload-complete-message.component';

describe('UploadCompleteMessageComponent', () => {
  let component: UploadCompleteMessageComponent;
  let fixture: ComponentFixture<UploadCompleteMessageComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ UploadCompleteMessageComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(UploadCompleteMessageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
