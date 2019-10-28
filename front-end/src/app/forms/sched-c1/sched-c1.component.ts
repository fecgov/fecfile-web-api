import { Component, OnInit, Input, Output, EventEmitter, SimpleChanges, OnChanges } from '@angular/core';
import { FormGroup, FormBuilder, FormControl, Validators } from '@angular/forms';
import { ScheduleActions } from '../form-3x/individual-receipt/schedule-actions.enum';
import { ContactsService } from 'src/app/contacts/service/contacts.service';
import { alphaNumeric } from 'src/app/shared/utils/forms/validation/alpha-numeric.validator';

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
  @Output() status: EventEmitter<any> = new EventEmitter<any>();

  public c1Form: FormGroup;
  public sectionType: string;
  public states: [];
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

  constructor(private _fb: FormBuilder, private _contactsService: ContactsService) {}

  public ngOnInit() {
    this.sectionType = Sections.initialSection;
    this._getStates();
    this._setFormGroup();
  }

  public ngOnChanges(changes: SimpleChanges) {
    this._clearFormValues();
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
    switch (this.sectionType) {
      case Sections.initialSection:
        if (this._checkSectionValid()) {
          this.sectionType = Sections.sectionA;
        }
        break;
      case Sections.sectionA:
        this.sectionType = Sections.sectionB;
        break;
      case Sections.sectionB:
        this.sectionType = Sections.sectionC;
        break;
      case Sections.sectionC:
        this.sectionType = Sections.sectionD;
        break;
      case Sections.sectionD:
        this.sectionType = Sections.sectionE;
        break;
      case Sections.sectionE:
        this.sectionType = Sections.sectionF;
        break;
      case Sections.sectionF:
        this.sectionType = Sections.sectionG;
        break;
      case Sections.sectionG:
        this.sectionType = Sections.sectionH;
        break;
      case Sections.sectionH:
        this.sectionType = Sections.sectionI;
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
        break;
      case Sections.sectionA:
        // TODO add method for checking section for valid fields before progressing
        return true;
        break;
      default:
        return false;
    }
  }

  private _checkInitialSectionValid(): boolean {
    // TODO check for valid form fields
    return true;
  }

  private _getStates() {
    this._contactsService.getStates().subscribe(res => {
      this.states = res;
      // this._setFormGroup();
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
      treasurer_signed_date: new FormControl(null, [Validators.required])
    });
  }

  public print() {
    alert('Print not yet implemented');
  }

  public finish() {
    alert('Finish not yet implemented');
  }

  public uploadFile() {
    // TODO add file to form
    // Is this neeed or can it be added to form from the html template
  }

  private _clearFormValues() {
    this.c1Form.reset();
  }
}
