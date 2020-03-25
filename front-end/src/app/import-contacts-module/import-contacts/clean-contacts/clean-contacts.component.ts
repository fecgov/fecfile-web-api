import { Component, OnInit, ViewEncapsulation, ChangeDetectionStrategy } from '@angular/core';
import { ImportContactsService } from '../service/import-contacts.service';
import { PaginationInstance } from 'ngx-pagination';
import { ContactToCleanModel } from './model/contact-to-clean.model';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { UtilService } from 'src/app/shared/utils/util.service';
import { BehaviorSubject, Observable } from 'rxjs';

@Component({
  selector: 'app-clean-contacts',
  templateUrl: './clean-contacts.component.html',
  styleUrls: ['./clean-contacts.component.scss'],
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class CleanContactsComponent implements OnInit {

  // public contacts: Array<ContactModel>;
  public contacts: Array<any>;
  public contacts$: Observable<Array<any>>;
  public contactToClean: Array<ContactToCleanModel>;
  public existingEntryHead: any;
  public newEntryHead: any;

  // ngx-pagination config
  public maxItemsPerPage = 10;
  public directionLinks = false;
  public autoHide = true;
  public config: PaginationInstance;
  public numberOfPages = 0;

  private contactsSubject: BehaviorSubject<Array<any>>;
  private readonly contactFields = [
    { displayName: 'Last Name', name: 'last_name' },
    { displayName: 'First Name', name: 'first_name' },
    { displayName: 'Organization', name: 'entity_name' },
    { displayName: 'Address 1', name: 'street1' },
    { displayName: 'Address 2', name: 'street2' },
    { displayName: 'City', name: 'city' },
    { displayName: 'State', name: 'state' },
    { displayName: 'Zip Code', name: 'zip' },
    { displayName: 'Occupation', name: 'occupation' },
    { displayName: 'Employer', name: 'employer' }
  ];

  constructor(
    private _importContactsService: ImportContactsService,
    private _modalService: NgbModal,
    private _utilService: UtilService
  ) { }

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
    this.initMergeHeaders();
    this.getContacts(1);
  }

  private initMergeHeaders() {
    this.existingEntryHead = {
      selected: false,
      disabled: false
    };
    this.newEntryHead = {
      selected: false,
      disabled: false
    };
  }

  public getContacts(page: number) {
    this.config.currentPage = page;
    this._importContactsService.getDuplicates(page).subscribe((res: any) => {
      // this.contacts = res.duplicates; // this us for default change detection strategy.
      this.contactsSubject.next(res.duplicates);
      this.config.totalItems = res.totalCount ? res.totalCount : 0;
      this.config.itemsPerPage = res.itemsPerPage ? res.itemsPerPage : this.maxItemsPerPage;
      this.numberOfPages = res.totalPages;
    });
  }

  public cleanContact(contact: any, modal: any) {
    this.prepareContactToClean(contact);
    this._modalService.open(modal, { size: 'lg', centered: true, backdrop: 'static' });
  }

  private prepareContactToClean(contact: any) {
    this.contactToClean = [];
    this.initMergeHeaders();
    for (const field of this.contactFields) {
      const model = new ContactToCleanModel();
      model.displayName = field.displayName;
      model.name = field.name;
      model.existingEntry = {
        value: contact[field.name],
        selected: false,
        disabled: false
      };
      let newEntryVal = null;
      if (contact.userContact) {
        newEntryVal = contact.userContact[field.name];
      }
      const originallyEmpty = this.isStringEmpty(newEntryVal);
      model.newEntry = {
        value: newEntryVal,
        selected: false,
        disabled: false,
        originallyEmpty: originallyEmpty
      };
      model.finalEntry = null;
      this.contactToClean.push(model);
    }
  }

  /**
   * Return true if merge is valid.  All fields must be selected from existing or new contact.
   */
  public checkMergeValid(): boolean {
    if (this.contactToClean) {
      for (const field of this.contactToClean) {
        if (field.existingEntry.selected === false &&
          field.newEntry.selected === false) {
          return false;
        }
      }
      return true;
    } else {
      return true;
    }
  }

  ///////////////////
  // merge methods
  ///////////////////

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

  ///////////////////
  // import methods
  ///////////////////

  public confirmFinalizeImport(modal: any) {
    // const contact0 = this.contacts[0];
    // this.contacts[0] = { ...contact0, entity_name: new Date().toString() };
    this._modalService.open(modal, { centered: true, backdrop: 'static' });
  }

  public cancelFinalizeImport(modal: any) {
    modal.close('cancel it');
    // this.cancelMerge();
  }

  public import(modal: any) {
    modal.close('close it');
    // TODO call API to save imported data for the file ID.
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

  public useAllExistingEntry($event: any) {
    if ($event.target.checked === true) {
      this.newEntryHead.disabled = true;
      for (const field of this.contactToClean) {
        field.existingEntry.selected = true;
        field.existingEntry.disabled = false;
        field.newEntry.disabled = true;
        field.newEntry.selected = false;
        field.finalEntry = field.existingEntry.value;
      }
    } else if ($event.target.checked === false) {
      this.newEntryHead.disabled = false;
      for (const field of this.contactToClean) {
        field.existingEntry.selected = false;
        field.newEntry.disabled = false;
        if (field.newEntry.selected) {
          field.finalEntry = field.newEntry.value;
        } else {
          field.finalEntry = null;
        }
      }
    }
  }

  public useAllNewEntry($event: any) {
    if ($event.target.checked === true) {
      this.existingEntryHead.disabled = true;
      for (const field of this.contactToClean) {
        field.newEntry.selected = true;
        field.newEntry.disabled = false;
        field.existingEntry.disabled = true;
        field.existingEntry.selected = false;
        field.finalEntry = field.newEntry.value;
      }
    } else if ($event.target.checked === false) {
      this.existingEntryHead.disabled = false;
      for (const field of this.contactToClean) {
        field.newEntry.selected = false;
        field.existingEntry.disabled = false;
        if (field.existingEntry.selected) {
          field.finalEntry = field.existingEntry.value;
        } else {
          field.finalEntry = null;
        }
      }
    }
  }

  public newFieldSelectedChange($event: any, field: ContactToCleanModel) {
    if ($event.target.checked === true) {
      field.existingEntry.disabled = true;
      field.finalEntry = field.newEntry.value;
    } else {
      field.existingEntry.disabled = false;
      field.finalEntry = null;
    }
  }

  public existingFieldSelectedChange($event: any, field: ContactToCleanModel) {
    if ($event.target.checked === true) {
      field.newEntry.disabled = true;
      field.finalEntry = field.existingEntry.value;
    } else {
      field.newEntry.disabled = false;
      field.finalEntry = null;
    }
  }

  public isStringEmpty(val: string) {
    return this._utilService.isStringEmpty(val);
  }

  public applyUserEditToFinal($event: any, field: ContactToCleanModel): void {
    if (field.newEntry.originallyEmpty) {
      if (field.newEntry.selected) {
        field.finalEntry = $event.target.value;
      }
    }
  }

}
