import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ImportTrxReviewComponent } from './import-trx-review.component';

describe('ImportTrxReviewComponent', () => {
  let component: ImportTrxReviewComponent;
  let fixture: ComponentFixture<ImportTrxReviewComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ImportTrxReviewComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ImportTrxReviewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
