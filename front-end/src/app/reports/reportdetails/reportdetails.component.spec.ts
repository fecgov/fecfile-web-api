import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ReportdetailsComponent } from './reportdetails.component';

describe('ReportdetailsComponent', () => {
  let component: ReportdetailsComponent;
  let fixture: ComponentFixture<ReportdetailsComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ ReportdetailsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ReportdetailsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
