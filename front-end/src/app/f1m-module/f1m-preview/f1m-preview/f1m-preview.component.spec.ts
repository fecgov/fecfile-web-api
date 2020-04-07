import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { F1mPreviewComponent } from './f1m-preview.component';

describe('F1mPreviewComponent', () => {
  let component: F1mPreviewComponent;
  let fixture: ComponentFixture<F1mPreviewComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ F1mPreviewComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(F1mPreviewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
