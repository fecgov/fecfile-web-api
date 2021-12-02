import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ImportFecfileSuccessComponent } from './import-fecfile-success.component';

describe('ImportFecfileSuccessComponent', () => {
  let component: ImportFecfileSuccessComponent;
  let fixture: ComponentFixture<ImportFecfileSuccessComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ ImportFecfileSuccessComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ImportFecfileSuccessComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
