import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ImportFecfileComponent } from './import-fecfile.component';

describe('ImportFecfileComponent', () => {
  let component: ImportFecfileComponent;
  let fixture: ComponentFixture<ImportFecfileComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ ImportFecfileComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ImportFecfileComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
