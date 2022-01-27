import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ReviewUploadComponent } from './review-upload.component';

describe('ReviewUploadComponent', () => {
  let component: ReviewUploadComponent;
  let fixture: ComponentFixture<ReviewUploadComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ ReviewUploadComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ReviewUploadComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
