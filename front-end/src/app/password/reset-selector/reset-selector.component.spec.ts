import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ResetSelectorComponent } from './reset-selector.component';

describe('ResetSelectorComponent', () => {
  let component: ResetSelectorComponent;
  let fixture: ComponentFixture<ResetSelectorComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ ResetSelectorComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ResetSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
