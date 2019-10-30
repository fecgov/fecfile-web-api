import { Component, OnInit, Input, Output, EventEmitter, SimpleChanges, OnChanges } from '@angular/core';
import { FormGroup, FormBuilder, FormControl, Validators } from '@angular/forms';
import { ScheduleActions } from '../form-3x/individual-receipt/schedule-actions.enum';
import { ContactsService } from 'src/app/contacts/service/contacts.service';
import { alphaNumeric } from 'src/app/shared/utils/forms/validation/alpha-numeric.validator';
import { Observable } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { TypeaheadService } from 'src/app/shared/partials/typeahead/typeahead.service';
import { NgbTypeaheadSelectItemEvent } from '@ng-bootstrap/ng-bootstrap';

export enum Sections {
  initialSection = 'initial_section',
  sectionA = 'section_a',
  sectionB = 'section_b',
  sectionC = 'section_c',
  sectionD = 'section_d',
  sectionE = 'section_e',
  sectionF = 'section_f',
  sectionG = 'section_g',
  sectionH = 'section_h',
  sectionI = 'section_i'
}

@Component({
  selector: 'app-sched-c1',
  templateUrl: './sched-c1.component.html',
  styleUrls: ['./sched-c1.component.scss']
})
export class SchedC1Component implements OnInit, OnChanges {
  @Input() scheduleAction: ScheduleActions;
  @Input() forceChangeDetection: Date;
  @Output() status: EventEmitter<any> = new EventEmitter<any>();

  public c1Form: FormGroup;
  public sectionType: string;
  public states: any[];
  public readonly initialSection = Sections.initialSection;
  public readonly sectionA = Sections.sectionA;
  public readonly sectionB = Sections.sectionB;
  public readonly sectionC = Sections.sectionC;
  public readonly sectionD = Sections.sectionD;
  public readonly sectionE = Sections.sectionE;
  public readonly sectionF = Sections.sectionF;
  public readonly sectionG = Sections.sectionG;
  public readonly sectionH = Sections.sectionH;
  public readonly sectionI = Sections.sectionI;
  public file: any = null;
  public fileNameToDisplay: string = null;

  constructor(
    private _fb: FormBuilder,
    private _contactsService: ContactsService,
    private _typeaheadService: TypeaheadService
  ) {}

  public ngOnInit() {
    this.sectionType = Sections.initialSection;
    this._getStates();
    this._setFormGroup();
  }

  public ngOnChanges(changes: SimpleChanges) {
    this._clearFormValues();
    if (this.scheduleAction === ScheduleActions.edit) {
      // TODO populate form using API response from schedC.
    }
  }

  public formatSectionType() {
    switch (this.sectionType) {
      case Sections.sectionA:
        return 'Section A';
      case Sections.sectionB:
        return 'Section B';
      case Sections.sectionC:
        return 'Section C';
      case Sections.sectionD:
        return 'Section D';
      case Sections.sectionE:
        return 'Section E';
      case Sections.sectionF:
        return 'Section F';
      case Sections.sectionG:
        return 'Section G';
      case Sections.sectionH:
        return 'Section H';
      case Sections.sectionI:
        return 'Section I';
      default:
        return '';
    }
  }

  /**
   * Validate section before proceeding to the next.
   */
  public showNextSection() {
    // Mark as touched if user clicks next on an untouched, invalid form
    // to display fields in error.
    this.c1Form.markAsTouched();

    switch (this.sectionType) {
      case Sections.initialSection:
        if (this._checkSectionValid()) {
          // mark as untouched so fields on new section/screen do not show as invalid
          this.c1Form.markAsUntouched();
          this.sectionType = Sections.sectionA;
        }
        break;
      case Sections.sectionA:
        if (this._checkSectionValid()) {
          // mark as untouched so fields on new section/screen do not show as invalid
          this.c1Form.markAsUntouched();
          this.sectionType = Sections.sectionB;
        }
        break;
      case Sections.sectionB:
        if (this._checkSectionValid()) {
          // mark as untouched so fields on new section/screen do not show as invalid
          this.c1Form.markAsUntouched();
          this.sectionType = Sections.sectionC;
        }
        break;
      case Sections.sectionC:
        if (this._checkSectionValid()) {
          // mark as untouched so fields on new section/screen do not show as invalid
          this.c1Form.markAsUntouched();
          this.sectionType = Sections.sectionD;
        }
        break;
      case Sections.sectionD:
        if (this._checkSectionValid()) {
          // mark as untouched so fields on new section/screen do not show as invalid
          this.c1Form.markAsUntouched();
          this.sectionType = Sections.sectionE;
        }
        break;
      case Sections.sectionE:
        if (this._checkSectionValid()) {
          // mark as untouched so fields on new section/screen do not show as invalid
          this.c1Form.markAsUntouched();
          this.sectionType = Sections.sectionF;
        }
        break;
      case Sections.sectionF:
        if (this._checkSectionValid()) {
          // mark as untouched so fields on new section/screen do not show as invalid
          this.c1Form.markAsUntouched();
          this.sectionType = Sections.sectionG;
        }
        break;
      case Sections.sectionG:
        if (this._checkSectionValid()) {
          // mark as untouched so fields on new section/screen do not show as invalid
          this.c1Form.markAsUntouched();
          this.sectionType = Sections.sectionH;
        }
        break;
      case Sections.sectionH:
        if (this._checkSectionValid()) {
          // mark as untouched so fields on new section/screen do not show as invalid
          this.c1Form.markAsUntouched();
          this.sectionType = Sections.sectionI;
        }
        break;
      default:
        this.sectionType = Sections.initialSection;
    }
  }

  /**
   * Show previous section.  No need to validate.
   */
  public showPreviousSection() {
    switch (this.sectionType) {
      case Sections.sectionA:
        this.sectionType = Sections.initialSection;
        break;
      case Sections.sectionB:
        this.sectionType = Sections.sectionA;
        break;
      case Sections.sectionC:
        this.sectionType = Sections.sectionB;
        break;
      case Sections.sectionD:
        this.sectionType = Sections.sectionC;
        break;
      case Sections.sectionE:
        this.sectionType = Sections.sectionD;
        break;
      case Sections.sectionF:
        this.sectionType = Sections.sectionE;
        break;
      case Sections.sectionG:
        this.sectionType = Sections.sectionF;
        break;
      case Sections.sectionH:
        this.sectionType = Sections.sectionG;
        break;
      case Sections.sectionI:
        this.sectionType = Sections.sectionH;
        break;
      default:
      // this.sectionType = Sections.initialSection;
    }
  }

  private _checkSectionValid(): boolean {
    switch (this.sectionType) {
      case Sections.initialSection:
        return this._checkInitialSectionValid();
      case Sections.sectionA:
        return this._checkSectionAValid();
      case Sections.sectionB:
        return this._checkSectionBValid();
      case Sections.sectionC:
        return this._checkSectionCValid();
      case Sections.sectionD:
        return this._checkSectionDValid();
      case Sections.sectionE:
        return this._checkSectionEValid();
      case Sections.sectionF:
        return this._checkSectionFValid();
      case Sections.sectionG:
        return this._checkSectionGValid();
      case Sections.sectionH:
        return this._checkSectionHValid();
      default:
        return true;
    }
  }

  private _checkInitialSectionValid(): boolean {
    // comment out for ease of dev testing - add back later.
    if (!this._checkFormFieldIsValid('lending_institution')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('mailing_address')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('city')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('state')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('zip')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('original_loan_amount')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('loan_intrest_rate')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('loan_incurred_date')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('loan_due_date')) {
      return false;
    }
    return true;
  }

  private _checkSectionAValid(): boolean {
    if (!this._checkFormFieldIsValid('is_loan_restructured')) {
      return false;
    }
    return true;
  }

  private _checkSectionBValid(): boolean {
    if (!this._checkFormFieldIsValid('credit_amount_this_draw')) {
      return false;
    }
    return true;
  }

  private _checkSectionCValid(): boolean {
    if (!this._checkFormFieldIsValid('other_parties_liable')) {
      return false;
    }
    return true;
  }

  private _checkSectionDValid(): boolean {
    if (!this._checkFormFieldIsValid('pledged_collateral_ind')) {
      return false;
    }
    return true;
  }

  private _checkSectionEValid(): boolean {
    if (!this._checkFormFieldIsValid('future_income_ind')) {
      return false;
    }
    return true;
  }

  private _checkSectionFValid(): boolean {
    if (!this._checkFormFieldIsValid('basis_of_loan_desc')) {
      return false;
    }
    return true;
  }

  private _checkSectionGValid(): boolean {
    if (!this._checkFormFieldIsValid('treasurer_last_name')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('treasurer_first_name')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('treasurer_middle_name')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('treasurer_prefix')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('treasurer_suffix')) {
      return false;
    }
    if (!this._checkFormFieldIsValid('treasurer_signed_date')) {
      return false;
    }
    return true;
  }

  private _checkSectionHValid(): boolean {
    if (!this._checkFormFieldIsValid('file_upload')) {
      return false;
    }
    return true;
  }

  private _checkSectionIValid(): boolean {
    if (!this._checkFormFieldIsValid('final_authorization')) {
      return false;
    }
    return true;
  }

  /**
   * Returns true if the field is valid.
   * @param fieldName name of control to check for validity
   */
  private _checkFormFieldIsValid(fieldName: string): boolean {
    if (this.c1Form.contains(fieldName)) {
      return this.c1Form.get(fieldName).valid;
    }
  }

  private _getStates() {
    this._contactsService.getStates().subscribe(res => {
      this.states = res;
    });
  }

  private _setFormGroup() {
    const alphaNumericFn = alphaNumeric();

    this.c1Form = this._fb.group({
      lending_institution: new FormControl(null, [Validators.required, Validators.maxLength(100)]),
      mailing_address: new FormControl(null, [Validators.required, Validators.maxLength(100)]),
      city: new FormControl(null, [Validators.required, Validators.maxLength(100), alphaNumericFn]),
      state: new FormControl(null, [Validators.required, Validators.maxLength(2)]),
      zip: new FormControl(null, [Validators.required, Validators.maxLength(10), alphaNumericFn]),
      original_loan_amount: new FormControl(null, [Validators.required, Validators.maxLength(12)]),
      loan_intrest_rate: new FormControl(null, [Validators.required, Validators.maxLength(2)]),
      loan_incurred_date: new FormControl(null, [Validators.required]),
      loan_due_date: new FormControl(null, [Validators.required]),
      is_loan_restructured: new FormControl(null, [Validators.required]),
      credit_amount_this_draw: new FormControl(null, [Validators.required, Validators.maxLength(12)]),
      total_outstanding_balance: new FormControl(null),
      other_parties_liable: new FormControl(null, [Validators.required]),
      pledged_collateral_ind: new FormControl(null, [Validators.required]),
      future_income_ind: new FormControl(null, [Validators.required]),
      basis_of_loan_desc: new FormControl(null, [Validators.required, Validators.maxLength(100)]),
      treasurer_last_name: new FormControl(null, [Validators.required, Validators.maxLength(30), alphaNumericFn]),
      treasurer_first_name: new FormControl(null, [Validators.required, Validators.maxLength(20), alphaNumericFn]),
      treasurer_middle_name: new FormControl(null, [Validators.maxLength(20), alphaNumericFn]),
      treasurer_prefix: new FormControl(null, [Validators.maxLength(10), alphaNumericFn]),
      treasurer_suffix: new FormControl(null, [Validators.maxLength(10), alphaNumericFn]),
      treasurer_signed_date: new FormControl(null, [Validators.required]),
      file_upload: new FormControl(null, [Validators.required]),
      final_authorization: new FormControl(null, [Validators.requiredTrue])
    });
  }

  public print() {
    alert('Print not yet implemented');
  }

  public finish() {
    if (this._checkSectionIValid()) {
      alert('Finish not yet implemented');
    } else {
      this.c1Form.markAsTouched();
    }
  }

  public uploadFile() {
    // TODO add file to form
    // Is this neeed or can it be added to form from the html template
  }

  private _clearFormValues() {
    this.c1Form.reset();
  }

  // type ahead start
  // type ahead start
  // type ahead start

  /**
   *
   * @param $event
   */
  public handleSelectedIndividual($event: NgbTypeaheadSelectItemEvent) {
    // TODO set entity id? in formGroup
    const entity = $event.item;
    this.c1Form.patchValue({ treasurer_last_name: entity.last_name }, { onlySelf: true });
    this.c1Form.patchValue({ treasurer_first_name: entity.first_name }, { onlySelf: true });
    this.c1Form.patchValue({ treasurer_middle_name: entity.middle_name }, { onlySelf: true });
    this.c1Form.patchValue({ treasurer_prefix: entity.prefix }, { onlySelf: true });
    this.c1Form.patchValue({ treasurer_suffix: entity.suffix }, { onlySelf: true });
  }

  /**
   * Format an entity to display in the type ahead.
   *
   * @param result formatted item in the typeahead list
   */
  public formatTypeaheadItem(result: any) {
    const lastName = result.last_name ? result.last_name.trim() : '';
    const firstName = result.first_name ? result.first_name.trim() : '';
    const street1 = result.street_1 ? result.street_1.trim() : '';
    const street2 = result.street_2 ? result.street_2.trim() : '';

    return `${lastName}, ${firstName}, ${street1}, ${street2}`;
  }

  /**
   * Search for entities/contacts when last name input value changes.
   */
  searchLastName = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        if (searchText) {
          return this._typeaheadService.getContacts(searchText, 'last_name');
        } else {
          return Observable.of([]);
        }
      })
    );

  /**
   * Search for entities/contacts when first name input value changes.
   */
  searchFirstName = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        if (searchText) {
          return this._typeaheadService.getContacts(searchText, 'first_name');
        } else {
          return Observable.of([]);
        }
      })
    );

  /**
   * format the value to display in the input field once selected from the typeahead.
   *
   * For some reason this gets called for all typeahead fields despite the binding in the
   * template to the last name field.  In these cases return x to retain the value in the
   * input for the other typeahead fields.
   */
  formatterLastName = (x: { last_name: string }) => {
    if (typeof x !== 'string') {
      return x.last_name;
    } else {
      return x;
    }
  };

  /**
   * format the value to display in the input field once selected from the typeahead.
   *
   * For some reason this gets called for all typeahead fields despite the binding in the
   * template to the first name field.  In these cases return x to retain the value in the
   * input for the other typeahead fields.
   */
  formatterFirstName = (x: { first_name: string }) => {
    if (typeof x !== 'string') {
      return x.first_name;
    } else {
      return x;
    }
  };

  // type ahead end
  // type ahead end
  // type ahead end

  public setFile(e: any): void {
    if (e.target.files[0]) {
      this.c1Form.patchValue({ file_upload: e.target.files[0] }, { onlySelf: true });
    }
  }
}
