import { Component, OnInit, ViewEncapsulation, ChangeDetectionStrategy, OnDestroy } from '@angular/core';
import { ImportContactsService } from '../service/import-contacts.service';
import { Subject, BehaviorSubject, Observable } from 'rxjs';

@Component({
  selector: 'app-clean-contacts',
  templateUrl: './clean-contacts.component.html',
  styleUrls: ['./clean-contacts.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class CleanContactsComponent implements OnInit, OnDestroy {

  public showErrors$: Observable<boolean>;
  public showDuplicates$: Observable<boolean>;

  private showDuplicatesSubject: BehaviorSubject<boolean>;
  private showErrorsSubject: BehaviorSubject<boolean>;
  private onDestroy$ = new Subject();

  constructor(
    private _importContactsService: ImportContactsService
  ) { }

  public ngOnInit(): void {
    this.onDestroy$ = new Subject();

    this.showDuplicatesSubject = new BehaviorSubject<boolean>(false);
    this.showDuplicates$ = this.showDuplicatesSubject.asObservable();
    this.showDuplicatesSubject.next(false);

    this.showErrorsSubject = new BehaviorSubject<boolean>(false);
    this.showErrors$ = this.showErrorsSubject.asObservable();
    this.showErrorsSubject.next(false);

    this.determineComponentsToShow();
  }

  public ngOnDestroy(): void {
    this.onDestroy$.next(true);
    this.showDuplicatesSubject.unsubscribe();
    this.showErrorsSubject.unsubscribe();
  }

  public determineComponentsToShow() {
    const page = 1;
    let showErrs = false;
    this._importContactsService.validateContacts(page).takeUntil(this.onDestroy$).subscribe((res: any) => {
      if (res.validation_errors) {
        if (res.validation_errors.length > 0) {
          showErrs = true;
          this.showErrorsSubject.next(true);
        }
      }
      if (showErrs === false) {
        this._importContactsService.checkDuplicates(page).takeUntil(this.onDestroy$).subscribe((res2: any) => {
          if (res2.duplicates) {
            if (res2.duplicates.length > 0) {
              this.showDuplicatesSubject.next(true);
            }
          }
        });
      }

    });
  }

}
