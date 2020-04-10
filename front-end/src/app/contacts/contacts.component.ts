import { animate, style, transition, trigger } from '@angular/animations';
import { Component, OnInit, ViewEncapsulation, OnDestroy, Output, EventEmitter, Input, ChangeDetectionStrategy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ContactsMessageService } from './service/contacts-message.service';
import { ContactFilterModel } from './model/contacts-filter.model';
import { Subscription } from 'rxjs/Subscription';
import { ContactModel } from './model/contacts.model';
import { AuthService} from '../shared/services/AuthService/auth.service';

import { MessageService } from '../shared/services/MessageService/message.service';
import { Subject } from 'rxjs';

export enum ActiveView {
  contacts = 'contacts',
  recycleBin = 'recycleBin',
  edit = 'edit'
}

export enum FilterTypes {
  keyword = 'keyword',
  category = 'category',
  amount = 'amount',
  aggregateAmount = 'aggregateAmount',
  date = 'date',
  deletedDate = 'deletedDate',
  state = 'state',
  type = 'type',
  memoCode = 'memoCode',
  itemizations = 'itemizations'
}

/**
 * The parent component for contacts.
 */
@Component({
  selector: 'app-contacts',
  templateUrl: './contacts.component.html',
  styleUrls: ['./contacts.component.scss'],
  encapsulation: ViewEncapsulation.None,
  /* animations: [
    trigger('fadeInOut', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate(500, style({ opacity: 1 }))
      ]),
      transition(':leave', [
        animate(10, style({ opacity: 0 }))
      ])
    ])
  ] */
})
export class ContactsComponent implements OnInit, OnDestroy {
  @Output() sidebarSwitch: EventEmitter<any> = new EventEmitter<any>();
  @Output() showContact: EventEmitter<any> = new EventEmitter<any>();
  @Input() status: any;

  public formType = '';
  public reportId = '0';
  public view: ActiveView = ActiveView.contacts;
  public contactsView = ActiveView.contacts;
  public recycleBinView = ActiveView.recycleBin;
  public editView = ActiveView.edit;
  public isShowFilters = false;
  public searchText = '';
  public searchTextArray = [];
  public tagArray: any = [];
  public showSideBar: boolean = false;
  /**
   * Subscription for applying filters to the contacts obtained from
   * the server.
   */
  private applyFiltersSubscription: Subscription;

  /**
   * Subscription for showing the ContactsEditComponent.
   */
  private editContactSubscription: Subscription;

  /**
   * Subscription for showing all Contacts.
   */
  private showContactSubscription: Subscription;

  public transactionToEdit: ContactModel;

  private filters: ContactFilterModel = new ContactFilterModel();
  private readonly filtersLSK = 'contacts.filters';
  private onDestroy$ = new Subject();
  private keywordGroup: any = [];
  constructor(
    private _activatedRoute: ActivatedRoute,
    private _contactsMessageService: ContactsMessageService,
    private _router: Router,
    private _messageService: MessageService,
    private _authService: AuthService
  ) {
    this.applyFiltersSubscription = this._contactsMessageService.getApplyFiltersMessage()
      .subscribe(
        (message: any) => {

          this.determineTags(message);

          if (message.isClearKeyword) {
            this.clearSearch();
          } else {
            this.doSearch();
          }
        }
      );

    this.editContactSubscription = this._contactsMessageService.getEditContactMessage()
      .subscribe(
        (trx: ContactModel) => {
          this.transactionToEdit = trx;
          this.showEdit();
        }
      );

    this.showContactSubscription = this._contactsMessageService.getShowContactsMessage()
      .subscribe(
        message => {
          this.showContacts();
        }
      );
  }


  /**
   * Initialize the component.
   */
  public ngOnInit(): void {

    // If the filter was open on the last visit in the user session, open it.
    const filtersJson: string | null = localStorage.getItem(this.filtersLSK);
    let filters: ContactFilterModel;
    if (filtersJson !== null && filtersJson !== 'null') {
      filters = JSON.parse(filtersJson);
      if (filters) {
        if (filters.keywords) {
          if (filters.keywords.length > 0) {
            this.searchTextArray = filters.keywords;
            filters.show = true;
          }
        }
      }
    } else {
      filters = new ContactFilterModel();
    }
    if (filters.show === true) {
      this.showFilters();
    }
  }


  /**
   * A method to run when component is destroyed.
   */
  public ngOnDestroy(): void {
    this.applyFiltersSubscription.unsubscribe();
    this.editContactSubscription.unsubscribe();
    this.showContactSubscription.unsubscribe();
    this.onDestroy$.next(true);
  }


  /**
   * Based on the filter settings and search string, determine the "tags" to show.
   */
  private determineTags(message: any) {
    const filters = this.filters = message.filters;

    // new and changed added filters should go at the end.
    // unchanged should appear in the beginning.


    // State
    if (this.filters.filterStates.length > 0) {
      const stateGroup = [];

      // is tag showing? Then modify it is the curr position
      // TODO put type strings in constants file as an enumeration
      // They are also used in the filter component as well.

      let stateTag = false;
      for (const tag of this.tagArray) {
        if (tag.type === FilterTypes.state) {
          stateTag = true;
          for (const cat of filters.filterStates) {
            stateGroup.push(cat);
          }
          tag.group = stateGroup;
        }
      }
      // If tag is not already showing, add it to the tag array.
      if (!stateTag) {
        for (const cat of filters.filterStates) {
          stateGroup.push(cat);
        }
        this.tagArray.push({ type: FilterTypes.state, prefix: null, group: stateGroup });
      }
    } else {
      this.removeTagArrayItem(FilterTypes.state);
    }

    // type
    if (this.filters.filterTypes.length > 0) {
      const typeGroup = [];

      // is tag showing? Then modify it is the curr position
      // TODO put type strings in constants file as an enumeration
      // They are also used in the filter component as well.

      let typeTag = false;
      for (const tag of this.tagArray) {
        if (tag.type === FilterTypes.type) {
          typeTag = true;
          for (const cat of filters.filterTypes) {
            typeGroup.push(cat);
          }
          tag.group = typeGroup;
        }
      }
      // If tag is not already showing, add it to the tag array.
      if (!typeTag) {
        for (const cat of filters.filterTypes) {
          typeGroup.push(cat);
        }
        this.tagArray.push({ type: FilterTypes.type, prefix: null, group: typeGroup });
      }
    } else {
      this.removeTagArrayItem(FilterTypes.type);
    }
    /*
    // keywords
    if (this.filters.keywords.length > 0) {
      const keywordGroup = [];
  
      // is tag showing? Then modify it is the curr position
      // TODO put type strings in constants file as an enumeration
      // They are also used in the filter component as well.
  
      let typeTag = false;
      for (const tag of this.tagArray) {
        if (tag.type === FilterTypes.keyword) {
          typeTag = true;
          for (const cat of filters.filterKeywords) {
            keywordGroup.push(cat);
          }
          tag.group = keywordGroup;
        }
      }
      // If tag is not already showing, add it to the tag array.
      if (!typeTag) {
        for (const cat of filters.filterKeywords) {
          keywordGroup.push(cat);
        }
        this.tagArray.push({type: FilterTypes.keyword, prefix: null, group: keywordGroup});
      }
    } else {
      this.removeTagArrayItem(FilterTypes.keyword);
    } */

    this.filters = filters;
  }


  /**
   * Search contacts.
   */
  public search() {

    // Don't allow more than 12 filters
    if (this.searchTextArray.length > 12) {
      return;
    }

    // TODO emit search message to the table contacts component
    if (this.searchText) {

      this.searchTextArray.push(this.searchText);
      // this.tagArray.push({type: FilterTypes.keyword, prefix: null, group: [this.searchText]});
      //this.tagArray.push({type: FilterTypes.keyword, prefix: null, group: 'Contact_Search'});

      this._messageService.getMessage().takeUntil(this.onDestroy$).subscribe(res => {
        if (res === 'Filter deleted') {
          if (this.keywordGroup.length > 0) {
            /*while (this.keywordGroup.length > 0) {
              this.keywordGroup.pop();
            }*/
            //this.keywordGroup=[];

          }
        }
      });

      this._messageService.getMessage().subscribe(res => {
        if (res.hasOwnProperty('filterstatus')) {
          if (res.filterstatus === 'deleted') {
            if (this.keywordGroup.length > 0) {
              /*while (this.keywordGroup.length > 0) {
                this.keywordGroup.pop();
              }*/
              this.keywordGroup = [];

            }
          }
        }
      });

      // const contactFilter =localStorage.getItem(this.filtersLSK);
      //onsole.log("contactFilter =", contactFilter);

      if (this.keywordGroup.length === 0) {
        this.tagArray.push({ type: FilterTypes.keyword, prefix: null, group: this.keywordGroup });
        this.keywordGroup.push(this.searchText);
      } else {
        this.keywordGroup.push(this.searchText);
      }



      this.searchText = '';
    }

    //console.log(" before search this.tagArray =", this.tagArray);
    this.doSearch();
    //this.showFilters();
    this.isShowFilters = true;
    this.showSideBar = true;
  }


  /**
   * Clear the keyword search items
   */
  public clearSearch() {
    this.searchTextArray = [];
    this.tagArray = [];
    this.searchText = '';
    this.doSearch();
  }


  /**
 * Clear the keyword search items
 */
  public clearSearchAndFilters() {

    // send a message to remove the filters from UI.
    this._contactsMessageService.sendRemoveFilterMessage({ removeAll: true });

    // And reset the filter model for the search.
    this.filters = new ContactFilterModel();

    // then clear the keywords and run the search without filters or search keywords.
    this.clearSearch();
  }


  /**
   * Remove the search text from the array.
   *
   * @param index index in the array
   */
  public removeSearchText(tagText: string) {
    const index = this.searchTextArray.indexOf(tagText);
    if (index !== -1) {
      this.searchTextArray.splice(index, 1);
      this.doSearch();
    }
  }


  /**
   * Remove the state filter tag and inform the filter component to clear it.
   */
  public removeStateFilter(index: number, state: string) {
    this.filters.filterStates.splice(index, 1);
    this.removeFilter(FilterTypes.state, state);
  }

  /**
   * Remove the Deleted Date filter tag and inform the filter component to clear it.
   */
  public removeDateDeletedFilter(index: number, deletedDate: string) {
    //this.filters..splice(index, 1);
    this.removeFilter(FilterTypes.deletedDate, deletedDate);
  }


  public removeTypeFilter(index: number, type: string) {
    this.filters.filterTypes.splice(index, 1);
    this.removeFilter(FilterTypes.type, type);
  }
  /**
   * Remove the State filter tag and inform the filter component to clear it.
   */
  public removeCategoryFilter(index: number, category: string) {
    //this.filters.filterCategories.splice(index, 1);
    this.removeFilter(FilterTypes.category, category);
  }


  /**
   * Remove the Date filter tag and inform the filter component to clear it.
   */
  public removeDateFilter() {
    this.removeFilter('date', null);
  }


  /**
   * Remove the Amount filter tag and inform the filter component to clear it.
   */
  public removeAmountFilter() {

    this.removeFilter(FilterTypes.amount, null);
  }


  /**
   * Remove the Aggregate Amount filter tag and inform the filter component to clear it.
   */
  public removeAggregateAmountFilter() {

    this.removeFilter(FilterTypes.aggregateAmount, null);
  }


  public removeMemoFilter() {

    this.removeFilter(FilterTypes.memoCode, null);
  }


  /**
   * Remove the Itemized filter tag and inform the filter component to clear it.
   */
  public removeItemizationsFilter(index: number, item: string) {
    this.removeFilter(FilterTypes.itemizations, item);
  }


  /**
   * Inform the Filter Component to clear the filter settings for the given key/value.
   *
   * @param key
   * @param value
   */
  private removeFilter(key: string, value: string) {
    this._contactsMessageService.sendRemoveFilterMessage({ key: key, value: value });
    this.doSearch();
  }


  /**
   * When a user clicks the close filter tag, delete the tag from the
   * tagsArray and inform the filter component to reset the filter setting.
   *
   * @param type filter type
   * @param index position in the array if the filter type can have multiples
   * @param tagText the text displayed on the tag
   */
  public removeTag(type: FilterTypes, index: number, tagText: string) {
    switch (type) {
      case FilterTypes.type:
        this.removeTypeFilter(index, tagText);
        this.removeTagArrayGroupItem(type, index);
        break;
      case FilterTypes.state:
        this.removeStateFilter(index, tagText);
        this.removeTagArrayGroupItem(type, index);
        break;
      case FilterTypes.keyword:
        this.removeSearchText(tagText);
        this.removeSearchTagArrayItem(tagText);
        this.keywordGroup.pop(tagText);
        break;
      case FilterTypes.deletedDate:
        this.removeStateFilter(index, tagText);
        this.removeTagArrayGroupItem(type, index);
        break;
      default:
    }
  }

  /**
   * Remove the search keyword form the tagArray.
   */
  private removeSearchTagArrayItem(tagText: string) {
    let i = 0;
    for (const tag of this.tagArray) {
      if (tag.type === FilterTypes.keyword) {
        if (tag.group) {
          if (tag.group.length > 0) {
            if (tag.group[0] === tagText) {
              this.tagArray.splice(i, 1);
            }
          }
        }
      }
      i++;
    }
  }


  /**
   * Remove the entire object form the tagArray.
   */
  private removeTagArrayItem(type: FilterTypes) {
    let i = 0;
    let typeFound = false;
    for (const tag of this.tagArray) {
      if (tag.type === type) {
        typeFound = true;
        break;
      }
      i++;
    }
    if (typeFound) {
      this.tagArray.splice(i, 1);
    }
  }


  /**
   * An item in the tagsArray may have a group as an array where 1 item in the group array
   * is to be removed. If no group items exist after removing, the entire object
   * will be removed from the tagsArray.
   *
   * @param type filter type
   * @param index index of the group array to remove
   */
  private removeTagArrayGroupItem(type: FilterTypes, index: number) {
    let i = 0;
    for (const tag of this.tagArray) {
      if (tag.type === type) {
        if (tag.group) {
          if (tag.group.length > 0) {
            tag.group.splice(index, 1);
          }
        }
        // If no tags in the group, delete the item from the tagArray.
        if (tag.group.length === 0) {
          this.tagArray.splice(i, 1);
        }
        break;
      }
      i++;
    }
  }


  /**
   * Show the table of contacts in the recycle bin for the user.
   */
  public showRecycleBin() {
    this.view = ActiveView.recycleBin

    // Inform the filter component of the view change
    this._contactsMessageService.sendSwitchFilterViewMessage(ActiveView.recycleBin);

    //  alert('Recycle Bin functionality is not yet supported');
  }


  /**
   * Show the table of form contacts.
   */
  public showContacts() {
    this.view = ActiveView.contacts;

    // Inform the filter component of the view change
    this._contactsMessageService.sendSwitchFilterViewMessage(ActiveView.contacts);
  }

  /**
   * Show the table of form contacts.
   */
  public AddContacts() {
    this._router.navigate([`/addContact`]);
  }



  /**
   * Show edit for a single transaction.
   */
  public showEdit() {
    this.view = ActiveView.edit;
  }


  /**
   * Show the option to select/deselect columns in the table.
   */
  public showPinColumns() {
    this.showContacts();
    this._contactsMessageService.sendShowPinColumnMessage('show the Pin Col');
  }


  /**
   * Import contacts from an external file.
   */
  public doImport() {
    // this._router.navigate(['/contacts/import']);
    this._router.navigate(['/import-contacts']);
  }


  /**
   * Show filter options for contacts.
   */
  public showFilters() {
    this.isShowFilters = true;
    this.sidebarSwitch.emit(this.isShowFilters);

    if (this.showSideBar) {
      this.showSideBar = false;
    } else {
      this.showSideBar = true;
    }

  }


  /**
   * Show the categories and hide the filters.
   */
  public showCategories() {
    this.isShowFilters = false;
    this.showSideBar = false;
  }


  /**
   * Check if the view to show is Contacts.
   */
  public isContactViewActive() {
    return this.view === this.contactsView ? true : false;
  }


  /**
   * Check if the view to show is Recycle Bin.
   */
  public isRecycleBinViewActive() {
    return this.view === this.recycleBinView ? true : false;
  }


  /**
   * Check if the view to show is Edit.
   */
  public isEditViewActive() {
    return this.view === this.editView ? true : false;
  }


  /**
   * Send a message to the subscriber to run the search.
   */
  private doSearch() {
    this.filters.keywords = this.searchTextArray;
    this._contactsMessageService.sendDoKeywordFilterSearchMessage(this.filters);
  }

  public onNotify(e): void {
    if (!e.editView) {
      this.view = ActiveView.contacts
    }
  }

}
