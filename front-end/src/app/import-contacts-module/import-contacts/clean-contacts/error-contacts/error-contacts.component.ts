import { Component, OnInit, ViewEncapsulation, ChangeDetectionStrategy, OnDestroy, Output, EventEmitter } from '@angular/core';
import { ImportContactsService } from '../../service/import-contacts.service';
import { PaginationInstance } from 'ngx-pagination';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { UtilService } from 'src/app/shared/utils/util.service';
import { BehaviorSubject, Observable, Subject } from 'rxjs';

@Component({
  selector: 'app-error-contacts',
  templateUrl: './error-contacts.component.html',
  styleUrls: ['./error-contacts.component.scss'],
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ErrorContactsComponent implements OnInit, OnDestroy {

  public contacts$: Observable<Array<any>>;

  // ngx-pagination config for the duplicates table of contacts
  public maxItemsPerPage = 10;
  public directionLinks = false;
  public autoHide = true;
  public config: PaginationInstance;
  public numberOfPages = 0;

  public mergePage: number;
  public mergePaginateConfig: PaginationInstance;

  private contactsSubject: BehaviorSubject<Array<any>>;
  private onDestroy$ = new Subject();

  constructor(
    private _importContactsService: ImportContactsService,
    private _modalService: NgbModal,
    private _utilService: UtilService
  ) { }

  ngOnInit() {
    this.contactsSubject = new BehaviorSubject<any>([]);
    this.contacts$ = this.contactsSubject.asObservable();
    const config: PaginationInstance = {
      id: 'error_contacts__table-pagination',
      itemsPerPage: this.maxItemsPerPage,
      currentPage: 1
    };
    this.config = config;
    this.validateContacts(1);
    this.mergePage = 1;
  }

  ngOnDestroy(): void {
    this.onDestroy$.next(true);
    this.contactsSubject.unsubscribe();
  }

  public validateContacts(page: number) {
    this.config.currentPage = page;
    this._importContactsService.validateContacts(page).takeUntil(this.onDestroy$).subscribe((res: any) => {
      this.contactsSubject.next(res.validation_errors);
      this.config.totalItems = res.totalCount ? res.totalCount : 0;
      this.config.itemsPerPage = res.itemsPerPage ? res.itemsPerPage : this.maxItemsPerPage;
      this.numberOfPages = res.totalPages;
    });
  }

  /**
   * Determine if pagination should be shown.
   */
  public showPagination(): boolean {
    if (this.config.totalItems > this.config.itemsPerPage) {
      return true;
    }
    // otherwise, no show.
    return false;
  }

}
