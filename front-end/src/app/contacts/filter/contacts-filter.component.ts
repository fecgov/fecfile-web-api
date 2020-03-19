import { Component, EventEmitter, Input, OnInit, Output, ViewChild, ElementRef, ViewChildren, QueryList, OnDestroy , ChangeDetectionStrategy } from '@angular/core';
import { style, animate, transition, trigger, state } from '@angular/animations';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { ContactsMessageService } from '../service/contacts-message.service';
//import { OrderByPipe } from 'src/app/shared/pipes/order-by/order-by.pipe';
import { OrderByPipe } from '../../../app/shared/pipes/order-by/order-by.pipe';
import { filter } from 'rxjs/operators';
import { ContactFilterModel } from '../model/contacts-filter.model';
import { ValidationErrorModel } from '../model/validation-error.model';
import { ContactsService } from '../service/contacts.service';
import { ContactsFilterTypeComponent } from './filter-type/contacts-filter-type.component';
import { Subscription } from 'rxjs/Subscription';
import { FilterTypes, ActiveView } from '../contacts.component';
import { MessageService } from '../../shared/services/MessageService/message.service';

/**
 * A component for filtering contacts located in the sidebar.
 */
@Component({
  selector: 'app-contacts-filter',
  templateUrl: './contacts-filter.component.html',
  styleUrls: ['./contacts-filter.component.scss'],
  providers: [NgbTooltipConfig, OrderByPipe],
   animations: [
    trigger('openClose', [
      state('open', style({
        'max-height': '500px', // Set high to handle multiple scenarios.
        backgroundColor: 'white',
      })),
      state('closed', style({
        'max-height': '0',
        overflow: 'hidden',
        display: 'none',
        backgroundColor: '#AEB0B5'
      })),
      transition('open => closed', [
        animate('.25s ease')
      ]),
      transition('closed => open', [
        animate('.5s ease')
      ]),
    ]),
    trigger('openCloseScroll', [
      state('open', style({
        'max-height': '500px', // Set high to handle multiple scenarios.
        backgroundColor: 'white',
        'overflow-y': 'scroll'
      })),
      state('closed', style({
        'max-height': '0',
        overflow: 'hidden',
        display: 'none',
        backgroundColor: '#AEB0B5'
      })),
      state('openNoAnimate', style({
        'max-height': '500px',
        backgroundColor: 'white',
        'overflow-y': 'scroll'
      })),
      state('closedNoAnimate', style({
        'max-height': '0',
        overflow: 'hidden',
        display: 'none',
        backgroundColor: '#AEB0B5'
      })),
      transition('open => closed', [
        animate('.25s ease')
      ]),
      transition('closed => open', [
        animate('.5s ease')
      ]),
    ]),
  ] 
})
export class ContactsFilterComponent implements OnInit, OnDestroy {
  @Output() status: EventEmitter<any> = new EventEmitter<any>();

  @Input()
  public formType: string;

  @Input()
  public title = '';

  @ViewChildren('categoryElements')
  private categoryElements: QueryList<ContactsFilterTypeComponent>;

  public isHideStateFilter: boolean;
  public isHideTypeFilter: boolean;
  public isHideDeletedDateFilter: boolean;
  public states: any = [];
  public types: any = [];
  public dateFilterValidation: ValidationErrorModel;
  public deletedDateFilterValidation: ValidationErrorModel;
  public amountFilterValidation: ValidationErrorModel;
  public aggregateAmountFilterValidation: ValidationErrorModel;
  public filterDeletedDateFrom: Date = null;
  public filterDeletedDateTo: Date = null;

  /**
   * Subscription for removing selected filters.
   */
  private removeFilterSubscription: Subscription;

  /**
   * Subscription for switch filters for ActiveView of the traansaction table.
   */
  private switchFilterViewSubscription: Subscription;

  // TODO put in a contacts constants ts file for multi component use.
  private readonly filtersLSK = 'contacts.filters';
  private cachedFilters: ContactFilterModel = new ContactFilterModel();
  private msEdge = true;
  private view = ActiveView.contacts;

  constructor(
    private _contactsService: ContactsService,
    private _contactsMessageService: ContactsMessageService,
    private _messageService: MessageService,
  ) {
    this.removeFilterSubscription = this._contactsMessageService.getRemoveFilterMessage()
      .subscribe(
        (message: any) => {
          if (message) {
            if (message.removeAll) {
              this.clearFilters();
            } else {
              this.removeFilter(message);
            }
          }
        }
      );

      this.switchFilterViewSubscription = this._contactsMessageService.getSwitchFilterViewMessage()
      .subscribe(
        (message: ActiveView) => {
          switch (message) {
            case ActiveView.contacts:
              this.view = message;
              break;
            case ActiveView.recycleBin:
              this.view = message;
              break;
            default:
              this.view = ActiveView.contacts;
          }
        }
      );
  }


  /**
   * Initialize the component.
   */
  public ngOnInit(): void {

    this.msEdge = this.isEdge();
    this.isHideTypeFilter = true;
    this.isHideStateFilter = true;
    this.isHideDeletedDateFilter = true;
    this.initValidationErrors();

    this.applyFiltersCache();
    this.getStates();
    this.getTypes();

  }


  /**
   * A method to run when component is destroyed.
   */
  public ngOnDestroy(): void {
    this.removeFilterSubscription.unsubscribe();
    this.switchFilterViewSubscription.unsubscribe();
  }


  /**
   * Toggle visibility of the Type filter
   */
  public toggleTypeFilterItem() {
    this.isHideTypeFilter = !this.isHideTypeFilter;
  }


  


  /**
   * Toggle visibility of the State filter
   */
  public toggleStateFilterItem() {
    this.isHideStateFilter = !this.isHideStateFilter;
  }

  public toggleDeletedDateFilterItem() {
    this.isHideDeletedDateFilter = !this.isHideDeletedDateFilter;
  }

  /**
   * Toggle the direction of the filter collapsed or expanded
   * depending on the hidden state.
   *
   * @returns string of the class to apply
   */
  public toggleFilterDirection(isHidden: boolean) {
    return isHidden ? 'up-arrow-icon' : 'down-arrow-icon';
  }

  
  /**
   * Determine the state for scrolling.  The category tye wasn't displaying
   * properly in edge with animation.  If edge, don't apply the state with animation.
   */
  public determineScrollState(input:any) {
    if (this.msEdge) {
      return !this.isHideStateFilter ? 'openNoAnimate' : 'closedNoAnimate';
    } else {
      return !this.isHideStateFilter ? 'open' : 'closed';
    }
  }

  public determineScrollType(input:any) {
    if (this.msEdge) {
      return !this.isHideTypeFilter ? 'openNoAnimate' : 'closedNoAnimate';
    } else {
      return !this.isHideTypeFilter ? 'open' : 'closed';
    }
  }
 

  /**
   * Scroll to the Category Type in the list that contains the
   * value from the category search input.
   */
  public scrollToType(): void {

    this.clearHighlightedTypes();

    
    /*const typeMatches: Array<ContactsFilterTypeComponent> =
      this.categoryElements.filter(el => {
        return el.categoryType.text.toString().toLowerCase()
          .includes(this.filterCategoriesText.toLowerCase());
      });

    if (typeMatches.length > 0) {
      const scrollEl = typeMatches[0];
      if (this.msEdge) {
        scrollEl.elRef.nativeElement.scrollIntoView();
      } else {
        scrollEl.elRef.nativeElement.scrollIntoView(
          { behavior: 'smooth', block: 'center', inline: 'start' }
        );
      }
    }

    // TODO check if sequence is guaranteed to be preserved.
    for (const type of typeMatches) {
      type.categoryType.highlight = 'selected_row';
    }*/
  }


  /**
   * Determine if the browser is MS Edge.
   *
   * TODO put in util service
   */
  private isEdge(): boolean {
    const ua = window.navigator.userAgent;
    const edge = ua.indexOf('Edge/');
    if (edge > 0) {
      // Edge (IE 12+) => return version number
      // return parseInt(ua.substring(edge + 5, ua.indexOf('.', edge)), 10);
      return true;
    }
    return false;
  }


  /**
   * Send filter values to the table contacts component.
   * Set the filters.show to true indicating the filters have been altered.
   */
  public applyFilters(isClearKeyword: boolean) {

    if (!this.validateFilters()) {
      return;
    }

    const filters = new ContactFilterModel();
    let modified = false;
    //filters.formType = this.formType;

    // states
    const filterStates = [];
    for (const s of this.states) {
      if (s.selected) {
        filterStates.push(s.state_code);
        modified = true;
      }
    }
    filters.filterStates= filterStates;

    const filterTypes = [];
    for (const s of this.types) {
      if (s.selected) {
        filterTypes.push(s.type_code);
        modified = true;
      }
    }
    filters.filterTypes = filterTypes;


    filters.filterDeletedDateFrom = this.filterDeletedDateFrom;
    filters.filterDeletedDateTo = this.filterDeletedDateTo;
    if (this.filterDeletedDateFrom !== null) {
      modified = true;
    }
    if (this.filterDeletedDateTo !== null) {
      modified = true;
    }

    filters.show = modified;

    //console.log("filters = ", filters);
    filters.show = modified;
    this._contactsMessageService.sendApplyFiltersMessage({filters: filters, isClearKeyword: isClearKeyword});
  }


  /**
   * Clear all filter values.
   */
  private clearFilters() {

    this.initValidationErrors();

    // clear the scroll to input
   // this.filterCategoriesText = '';
    this.clearHighlightedTypes();


    for (const s of this.states) {
      s.selected = false;
    }

    for (const s of this.types) {
      s.selected = false;
    }


    this._messageService.sendMessage('Filter deleted');
    
    this.status.emit({
      filterstatus:'deleted'
    });


  }


  /**
   * Clear all filter values and apply them by running the search.
   */
  public clearAndApplyFilters() {
        this.clearFilters();
        this.applyFilters(true);
  }


  /**
   * Check if the view to show is Contacts.
   */
  public isContactViewActive() {
    return this.view === ActiveView.contacts ? true : false;
  }


  /**
   * Check if the view to show is Recycle Bin.
   */
  public isRecycleBinViewActive() {
    return this.view === ActiveView.recycleBin ? true : false;
  }


  /**
   * Clear any hightlighted types as result of the scroll to input.
   */
  private clearHighlightedTypes() {
    for (const el of this.categoryElements.toArray()) {
      el.categoryType.highlight = '';
    }
  }


  private getStates() {
    // TODO using this service to get states until available in another API.
    // Passing INDV_REC as type but any should do as states are not specific to
    // transaction type.
    this._contactsService.getStates().subscribe(res => {
      let statesExist = false;
      if (res) {
          statesExist = true;
          for (const s of res) {
            // check for states selected in the filter cache
            // TODO scroll to first check item
            if (this.cachedFilters) {
              if (this.cachedFilters.filterStates) {
                if (this.cachedFilters.filterStates.includes(s.state_code)) {
                  s.selected = true;
                  this.isHideStateFilter = false;
                } else {
                  s.selected = false;
                }
              }
          }
        }
      }
      if (statesExist) {
        this.states = res;
      } else {
        this.states = [];
      }
    });
    
  }

  private getTypes() {
    // TODO using this service to get Itemizations until available in another API.
    this._contactsService.getTypes().subscribe(res => {
      let typeExist = false;
      if (res.data) {
        typeExist = true;
        for (const s of res.data) {
          // check for Itemizations selected in the filter cache
          // TODO scroll to first check item
          if (this.cachedFilters) {
            if (this.cachedFilters.filterTypes) {
              if (this.cachedFilters.filterTypes.includes(s.type_code)) {
                s.selected = true;
                this.isHideTypeFilter = false;
              } else {
                s.selected = false;
              }
            }
          }
        }
      }
      if (typeExist) {
        this.types = res.data;
      } else {
        this.types = [];
      }
    });
  }

 
  /**
   * Get the filters from the cache.
   */
  private applyFiltersCache() {
    const filtersJson: string | null = localStorage.getItem(this.filtersLSK);
    if (filtersJson != null) {
      this.cachedFilters = JSON.parse(filtersJson);
      if (this.cachedFilters) {
        // Note state and type apply filters are handled after server call to get values.

        // TODO itenized was left out and needs to be added.
        this.types = this.cachedFilters.filterTypes;
        this.states = this.cachedFilters.filterStates;

        this.filterDeletedDateFrom = this.cachedFilters.filterDeletedDateFrom;
        this.filterDeletedDateTo = this.cachedFilters.filterDeletedDateTo;
        this.isHideDeletedDateFilter = (this.filterDeletedDateFrom && this.filterDeletedDateTo) ? false : true;

      }
    } else {
      // Just in case cache has an unexpected issue, use default.
      this.cachedFilters = new ContactFilterModel();
    }
  }


  /**
   * Initialize validation errors to their defaults.
   */
  private initValidationErrors() {
    this.dateFilterValidation = new ValidationErrorModel(null, false);
    this.deletedDateFilterValidation = new ValidationErrorModel(null, false);
    this.amountFilterValidation = new ValidationErrorModel(null, false);
    this.aggregateAmountFilterValidation = new ValidationErrorModel(null, false);
  }


  /**
   * Validate the filter settings.  Set the the validation error model
   * to true with a message if invalid.
   *
   * @returns true if valid.
   */
  private validateFilters(): boolean {

    this.initValidationErrors();
 
    return true;
  }


  /**
   * Process the message received to remove the filter.
   * 
   * @param message contains details on the filter to remove
   */
  private removeFilter(message: any) {
    if (message) {
      if (message.key) {
        switch (message.key) {
          case FilterTypes.state:
            for (const st of this.states) {
              if (st.state_code === message.value) {
                st.selected = false;
              }
            }
            break;
            case FilterTypes.type:
            for (const st of this.types) {

              if (st.type_code === message.value) {

                st.selected = false;
              }
            }
            break;  
          default:
        }
      }
    }
  }
  /*private validateFilters(): boolean {

    this.filterDeletedDateTo = this.handleDateAsSpaces(this.filterDeletedDateTo);
    this.filterDeletedDateFrom = this.handleDateAsSpaces(this.filterDeletedDateFrom);

    this.initValidationErrors();
    if (this.filterDeletedDateFrom !== null && this.filterDeletedDateTo === null) {
      this.deletedDateFilterValidation.isError = true;
      this.deletedDateFilterValidation.message = 'To Deleted Date is required';
      this.isHideDeletedDateFilter = false;
      return false;
    }
    if (this.filterDeletedDateTo !== null && this.filterDeletedDateFrom === null) {
      this.deletedDateFilterValidation.isError = true;
      this.deletedDateFilterValidation.message = 'From Deleted Date is required';
      this.isHideDeletedDateFilter = false;
      return false;
    }
    if (this.filterDeletedDateFrom > this.filterDeletedDateTo) {
      this.deletedDateFilterValidation.isError = true;
      this.deletedDateFilterValidation.message = 'From Deleted Date must preceed To Deleted Date';
      this.isHideDeletedDateFilter = false;
      return false;
    }
     return true;
  }*/

  private handleDateAsSpaces(date: any) {
    return date === '' ? null : date;
  }
}
