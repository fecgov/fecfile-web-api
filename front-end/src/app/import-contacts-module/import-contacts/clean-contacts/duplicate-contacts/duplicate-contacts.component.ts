import {
  Component,
  OnInit,
  ViewEncapsulation,
  ChangeDetectionStrategy,
  OnDestroy,
  Output,
  EventEmitter,
  Input
} from '@angular/core';
import { ImportContactsService } from '../../service/import-contacts.service';
import { PaginationInstance } from 'ngx-pagination';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { UtilService } from 'src/app/shared/utils/util.service';
import { BehaviorSubject, Observable, Subject } from 'rxjs';
import { FieldToCleanModel } from './model/field-to-clean.model';
import { FieldEntryModel } from './model/field-entry.model';
import { ImportContactModel } from '../../model/import-contact.model';
import { DuplicateContactsService } from './service/duplicate-contacts.service';

@Component({
  selector: 'app-duplicate-contacts',
  templateUrl: './duplicate-contacts.component.html',
  styleUrls: ['./duplicate-contacts.component.scss'],
  encapsulation: ViewEncapsulation.None
  // changeDetection: ChangeDetectionStrategy.OnPush
})
export class DuplicateContactsComponent implements OnInit, OnDestroy {
  @Input()
  public fileName: string;

  @Output()
  public dupeProceedEmitter: EventEmitter<any> = new EventEmitter<any>();

  @Output()
  public dupeCancelEmitter: EventEmitter<any> = new EventEmitter<any>();

  public contacts: Array<any>;
  public contacts$: Observable<Array<any>>;

  // ngx-pagination config for the duplicates table of contacts
  public maxItemsPerPage = 10;
  public directionLinks = false;
  public autoHide = true;
  public config: PaginationInstance;
  public numberOfPages = 0;

  /**
   * All fields and their values from the user's contact from the file and
   * all potential duplicates.
   */
  public fieldsToClean: Array<FieldToCleanModel>;

  public readonly duplicatePlaceHolder = 'dupe placeholder';

  public mergePage: number = 1;
  public mergePaginateConfig: PaginationInstance = {
    id: 'merge_dupes',
    itemsPerPage: 2,
    currentPage: this.mergePage
  };

  public userContactHeader: any;
  public dupeContactHeader: Array<any>;
  public totalDuplicates = 0;
  public allDupesSelected: boolean;

  private contactsSubject: BehaviorSubject<Array<any>>;
  private onDestroy$ = new Subject();

  private readonly contactFields = [
    { displayName: 'Committee ID', name: 'committeeId' },
    { displayName: 'Type', name: 'type' },
    { displayName: 'Committee Name/Organization', name: 'name' },
    { displayName: 'First Name', name: 'firstName' },
    { displayName: 'Last Name', name: 'lastName' },
    { displayName: 'Middle Name', name: 'middleName' },
    { displayName: 'Prefix', name: 'prefix' },
    { displayName: 'Suffix', name: 'suffix' },
    { displayName: 'Address 1', name: 'street' },
    { displayName: 'Address 2', name: 'street2' },
    { displayName: 'City', name: 'city' },
    { displayName: 'State', name: 'state' },
    { displayName: 'Zip Code', name: 'zip' },
    { displayName: 'Employer', name: 'employer' },
    { displayName: 'Occupation', name: 'occupation' },
    { displayName: 'Candidate ID', name: 'candidateId' },
    { displayName: 'Candidate Office', name: 'officeSought' },
    { displayName: 'Candidate State', name: 'officeState' },
    { displayName: 'Candidate District', name: 'district' },
    { displayName: 'Multi-Candidate Committee Status', name: 'multiCandidateCmteStatus' }
  ];

  constructor(
    private _importContactsService: ImportContactsService,
    private _duplicateContactsService: DuplicateContactsService,
    private _modalService: NgbModal,
    private _utilService: UtilService
  ) {}

  ngOnInit() {
    this.contacts = [];
    this.contactsSubject = new BehaviorSubject<any>([]);
    this.contacts$ = this.contactsSubject.asObservable();
    const config: PaginationInstance = {
      id: 'clean_contacts__table-pagination',
      itemsPerPage: this.maxItemsPerPage,
      currentPage: 1
    };
    this.config = config;
    this.checkDuplicates(1);
    this.mergePage = 1;
    this.allDupesSelected = false;
  }

  ngOnDestroy(): void {
    this.onDestroy$.next(true);
    this.contactsSubject.unsubscribe();
  }

  public checkDuplicates(page: number) {
    this.config.currentPage = page;

    // // this._importContactsService.checkDuplicates(page).takeUntil(this.contactsSubject).subscribe((res: any) => {
    // this._duplicateContactsService.getDuplicates_mock(page).subscribe((res: any) => {
    //   this.contactsSubject.next(res.duplicates);
    //   // this.contactsSubject.next(this.duplicates);
    //   this.config.totalItems = res.totalCount ? res.totalCount : 0;
    //   this.config.itemsPerPage = res.itemsPerPage ? res.itemsPerPage : this.maxItemsPerPage;
    //   this.numberOfPages = res.totalPages;
    // });

    this._duplicateContactsService.getDuplicates(this.fileName, page).subscribe((res: any) => {
      // // temp to set selected to false until api does
      // for (const contact of res.contacts) {
      //   for (const dupe of contact.contacts_from_db) {
      //     // TEMP CODE
      //     // response contacts the contact from DB the user may have identified as one to merge.
      //     // If user has done this, the user_selected_value on th CONTACT not the DUPE CONTACT
      //     // will contain the entity id of the selected contact.
      //     // Set a field on the DUPLICATE CONTACT for the UI
      //     // TODO change API to set select on the dupe. For now just set the first one for devl.
      //     dupe.user_selected_value = false;
      //     if (contact.user_selected_option !== 'add') {
      //       contact.contacts_from_db[0].user_selected_value = true;
      //     }
      //     // TEMP CDE END
      //   }
      // }

      this.contacts = res.contacts;
      this.config.totalItems = res.totalcontactsCount;
      this.config.itemsPerPage = res.itemsPerPage;
      this.numberOfPages = res.totalPages;
      this.allDupesSelected = res.allDone;
    });
  }

  public formatName(contact: any): string {
    let name = '';
    if (contact.entity_type === 'IND') {
      // TODO handle suffix and prefix
      name = `${contact.last_name}, ${contact.first_name}`;
    } else if (contact.entity_type === 'ORG') {
      name = contact.entity_name;
    }
    return name;
  }

  public cleanContact(contact: any, modal: any) {
    this.prepareContactToClean(contact);
    this._modalService.open(modal, { size: 'lg', centered: true, backdrop: 'static' });
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

  public proceed(): void {
    this.dupeProceedEmitter.emit('ignore_dupe_save');
  }

  ////////////////////////
  // merge modal methods
  ////////////////////////

  public cancelMerge(modal: any): void {
    modal.close('close it');
  }

  public merge(modal: any) {
    modal.close('close it');
    // TODO call API to save merge data for the file ID. use this.contactToClean
    // Either get the page data again from API removing the merged contact
    // or slice the merged contact out of the array.  Former is preferred.
  }

  public cancelFinalizeMerge(modal: any) {
    modal.close('cancel it');
    // this.cancelMerge();
  }

  public confirmFinalizeMerge(modal: any) {
    this._modalService.open(modal, { centered: true, backdrop: 'static' });
  }

  /////////////////////////
  // import all modal methods
  /////////////////////////

  public confirmFinalizeImportAll(modal: any) {
    // const contact0 = this.contacts[0];
    // this.contacts[0] = { ...contact0, entity_name: new Date().toString() };
    this._modalService.open(modal, { centered: true, backdrop: 'static' });
  }

  public cancelFinalizeImportAll(modal: any) {
    modal.close('cancel it');
  }

  public importAll(modal: any) {
    modal.close('close it');
    this.dupeProceedEmitter.emit('ignore_dupe_save');
  }

  /////////////////////////
  // merge modal methods
  /////////////////////////

  public confirmFinalizeMergeAll(modal: any) {
    this._modalService.open(modal, { centered: true, backdrop: 'static' });
  }

  public cancelFinalizeMergeAll(modal: any) {
    modal.close('cancel it');
  }

  public mergeAll(modal: any) {
    modal.close('close it');
    this.dupeProceedEmitter.emit('merge_dupe_save');
  }

  public cancelImportAll() {
    this.dupeCancelEmitter.emit();
    this._duplicateContactsService.cancelImport(this.fileName).subscribe((res: any) => {});
  }

  // TODO consider putting merge modal methods in another plain old class (not a component)
  // for code separation.

  /**
   * For possible duplicates with the incoming contact and the existing contacts in the system,
   * apply the users decision on how to handle.
   *
   * @param contact the contact to merge
   * @param userAction the merge action selected by the user
   */
  public applyMergeSelection(contact: any, userAction: string) {
    contact.user_selected_option = userAction;
    this._duplicateContactsService.saveUserMergeSelection(this.fileName, contact).subscribe((res: any) => {});
  }

  // No longer used
  // No longer used
  // No longer used
  // No longer used
  // No longer used
  // No longer used
  // No longer used
  // No longer used
  // No longer used
  // No longer used

  // Clean single contact methods start here
  // Clean single contact methods start here
  // Clean single contact methods start here

  private prepareContactToClean(contact: any) {
    // fill in placeholders for duplicates allowing for equal slots
    // for duplicate paginate.

    if (contact.potentialDupes) {
      if (Array.isArray(contact.potentialDupes)) {
        const remainder = contact.potentialDupes.length % this.mergePaginateConfig.itemsPerPage;
        if (remainder !== 0) {
          contact.potentialDupes.push(this.duplicatePlaceHolder);
        }
      }
    }

    this.mergePage = 1;
    this.fieldsToClean = [];
    this.initMergeHeaders(contact);
    for (const field of this.contactFields) {
      const model = new FieldToCleanModel();
      model.displayName = field.displayName;
      model.name = field.name;

      const userField = new FieldEntryModel();
      userField.value = contact[field.name];
      userField.originallyEmpty = this.isStringEmpty(userField.value);
      model.userField = userField;

      const dupes = new Array<FieldEntryModel>();
      for (const dupe of contact.potentialDupes) {
        if (dupe !== this.duplicatePlaceHolder) {
          const dupeField = new FieldEntryModel();
          dupeField.value = dupe[field.name];
          dupeField.originallyEmpty = this.isStringEmpty(dupeField.value);
          dupes.push(dupeField);
        } else {
          const dupeField = new FieldEntryModel();
          dupeField.value = dupe;
          dupes.push(dupeField);
        }
      }
      model.dupeFields = dupes;
      model.finalField = null;
      this.fieldsToClean.push(model);
    }
  }

  private createHeader(): any {
    return {
      selected: false,
      disabled: false
    };
  }

  private initMergeHeaders(contact: any) {
    this.userContactHeader = this.createHeader();

    this.totalDuplicates = 0;
    this.dupeContactHeader = [];
    for (const dupe of contact.potentialDupes) {
      if (dupe !== this.duplicatePlaceHolder) {
        const header = this.createHeader();
        header.seq = dupe.seq;
        this.dupeContactHeader.push(header);
        this.totalDuplicates++;
      } else {
        this.dupeContactHeader.push(dupe);
      }
    }
  }

  /**
   * Return true if merge is valid.  All fields must be selected from existing or new contact.
   */
  public checkMergeValid(): boolean {
    if (this.fieldsToClean) {
      for (const field of this.fieldsToClean) {
        let dupeFieldSelected = false;
        for (const dupe of field.dupeFields) {
          if (dupe.selected) {
            dupeFieldSelected = true;
          }
        }
        if (field.userField.selected === false && dupeFieldSelected === false) {
          return false;
        }
      }
      return true;
    } else {
      return true;
    }
  }

  public useAllDuplicate($event: any, i: number) {
    // clear out any previously checked fields
    i--;
    for (const field of this.fieldsToClean) {
      field.userField.selected = false;
      for (const dupe of field.dupeFields) {
        dupe.selected = false;
      }
      field.finalField = null;
    }
    if ($event.target.checked === true) {
      // uncheck all but the select duplicate header
      for (const dupeHeader of this.dupeContactHeader) {
        if (dupeHeader !== this.duplicatePlaceHolder) {
          dupeHeader.selected = false;
        }
      }
      this.userContactHeader.selected = false;
      this.dupeContactHeader[i].selected = true;

      for (const field of this.fieldsToClean) {
        field.dupeFields[i].selected = true;
        field.finalField = field.dupeFields[i].value;
      }
    } else {
      for (const field of this.fieldsToClean) {
        field.dupeFields[i].selected = false;
      }
    }
  }

  public useAllUserContact($event: any) {
    // clear out any previously checked fields
    for (const field of this.fieldsToClean) {
      for (const dupe of field.dupeFields) {
        dupe.selected = false;
      }
      field.finalField = null;
    }

    // toggle user fields selected/not-selected
    if ($event.target.checked === true) {
      for (const field of this.fieldsToClean) {
        field.userField.selected = true;
        field.finalField = field.userField.value;
      }
      // uncheck any duplicate headers checked
      for (const dupeHeader of this.dupeContactHeader) {
        if (dupeHeader !== this.duplicatePlaceHolder) {
          dupeHeader.selected = false;
        }
      }
    } else {
      for (const field of this.fieldsToClean) {
        field.userField.selected = false;
      }
    }
  }

  public fieldSelectedChange(field: FieldToCleanModel) {
    let final = '';
    if (field.userField.selected) {
      final = field.userField.value;
    }
    for (const dupe of field.dupeFields) {
      if (dupe.selected) {
        if (this.isStringEmpty(final)) {
          final += dupe.value;
        } else {
          final += ` / ${dupe.value}`;
        }
      }
      field.finalField = final;
    }
  }

  public isStringEmpty(val: string) {
    return this._utilService.isStringEmpty(val);
  }

  public applyUserEditToFinal(edittedField: FieldEntryModel, fieldToClean: FieldToCleanModel): void {
    if (edittedField.originallyEmpty) {
      if (edittedField.selected) {
        this.fieldSelectedChange(fieldToClean);
      }
    }
  }

  public checkLastDupeHeaderOnPage(i: number, header: any): boolean {
    if (i + 1 === this.mergePaginateConfig.itemsPerPage) {
      return true;
    } else {
      return false;
    }
  }

  public checkFirstDupeHeaderOnPage(i: number, header: any): boolean {
    if (i === 0) {
      return true;
    } else {
      return false;
    }
  }
}
