import { ChangeDetectionStrategy, Component, OnInit, Input } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, Validators } from '@angular/forms';
import { NgbTypeaheadSelectItemEvent } from '@ng-bootstrap/ng-bootstrap';
import { Observable } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { TypeaheadService } from './../../../shared/partials/typeahead/typeahead.service';

@Component({
  selector: 'app-f1m-affiliation',
  templateUrl: './f1m-affiliation.component.html',
  styleUrls: ['./f1m-affiliation.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class F1mAffiliationComponent implements OnInit {

  public form: FormGroup;
  public tooltipPlaceholder = "Placeholder text";

  constructor(
    private _fb: FormBuilder,
    private _typeaheadService: TypeaheadService
  ) { }

  ngOnInit() {
    this.initForm();
  }
  
  public initForm() {
    this.form = this._fb.group({
      affiliation_date: new FormControl(null, [Validators.required, Validators.maxLength(100)]),
      committee_id: new FormControl(null, [Validators.required, Validators.maxLength(9)]),
      committee_name: new FormControl(null, [Validators.required, Validators.maxLength(100)])
    });
  }

  /**
   * format the value to display in the input field once selected from the typeahead.
   */
  formatterCommitteeId = (x: { cmte_id: string }) => {
    if (typeof x !== 'string') {
      return x.cmte_id;
    } else {
      return x;
    }
  };

   /**
   * format the value to display in the input field once selected from the typeahead.
   */
  formatterCommitteeName = (x: { cmte_name: string }) => {
    if (typeof x !== 'string') {
      return x.cmte_name;
    } else {
      return x;
    }
  };

  /**
   * Search for entities when organization/entity_name input value changes.
   */
  searchCommitteeId = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        const searchTextUpper = searchText.toUpperCase();

        if (
          searchTextUpper === 'C' ||
          searchTextUpper === 'C0' ||
          searchTextUpper === 'C00' ||
          searchTextUpper === 'C000'
        ) {
          return Observable.of([]);
        }

        if (searchText) {
          return this._typeaheadService.getContacts(searchText, 'cmte_id');
        } else {
          return Observable.of([]);
        }
      })
    );

  /**
   * Search for entities when organization/entity_name input value changes.
   */
  searchCommitteeName = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(500),
      distinctUntilChanged(),
      switchMap(searchText => {
        if (searchText) {
          return this._typeaheadService.getContacts(searchText, 'cmte_name');
        } else {
          return Observable.of([]);
        }
      })
    );    
  

  /**
   * Format an entity to display in the Committee ID type ahead.
   * @param result formatted item in the typeahead list
   */
  public formatTypeaheadCommitteeId(result: any) {
    const street1 = result.street_1 ? result.street_1.trim() : '';
    const street2 = result.street_2 ? result.street_2.trim() : '';
    const name = result.cmte_id ? result.cmte_id.trim() : '';
    const cmteName = result.cmte_name ? result.cmte_name.trim() : '';
    return `${name},${cmteName},${street1}, ${street2}`;
  }

  /**
   * Format an entity to display in the Committee Name type ahead.
   *
   * @param result formatted item in the typeahead list
   */
  public formatTypeaheadCommitteeName(result: any) {
    const street1 = result.street_1 ? result.street_1.trim() : '';
    const street2 = result.street_2 ? result.street_2.trim() : '';
    const name = result.cmte_id ? result.cmte_name.trim() : '';

    return `${name}, ${street1}, ${street2}`;
  }

  /**
   * Populate the fields in the form with the values from the selected contact.
   *
   * @param $event The mouse event having selected the contact from the typeahead options.
   */
  public handleSelectedCommittee($event: NgbTypeaheadSelectItemEvent) {
    
    // preventDefault this is used so NgbTypeAhead doesn't automatically save the whole object on modal close
    $event.preventDefault(); 
    const entity = $event.item;
    this.form.patchValue({'committee_id':entity.cmte_id}, {onlySelf:true});
    this.form.patchValue({'committee_name':entity.cmte_name}, {onlySelf:true});

  }

}
