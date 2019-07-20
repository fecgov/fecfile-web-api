import { Component, Input, Output, EventEmitter } from '@angular/core';
import { ObservableInput, Observable, interval } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap, map, catchError } from 'rxjs/operators';
import { TypeaheadService } from './typeahead.service';

/**
 * This component is under development.  Remove it if it is not to be used.
 * Until it is ready use the type ahead diretly on an input element in your template.
 *
 */
@Component({
  selector: 'app-typeahead',
  templateUrl: './typeahead.component.html',
  styles: [
    `
      .form-control {
        width: 300px;
      }
    `
  ]
})
export class TypeaheadComponent {
  @Input() public fieldName: string;
  @Input() public columnProperties: any;
  @Output() selectedItem: EventEmitter<any> = new EventEmitter<any>();
  /**
   * TODO: Emit this data out to parent as output.
   */
  public model: any;

  /**
   *
   * @param _typeaheadService
   */
  constructor(private _typeaheadService: TypeaheadService) {}

  public formatTypeaheadItem(result: any) {
    return `${result.last_name}, ${result.first_name}, ${result.street_1}, ${result.street_2}`;
  }

  /**
   * Search for field when input changes.
   */
  search = (text$: Observable<string>) =>
    text$.pipe(
      debounceTime(200),
      distinctUntilChanged(),
      switchMap(searchText => {
        return this._typeaheadService.getContacts(searchText, this.fieldName);
      })
    );

  formatter = (x: { first_name: string; last_name: string }) => {
    this.selectedItem.emit(x);
    if (this.fieldName === 'first_name') {
      return x.first_name;
    } else {
      return x.last_name;
    }
  };

  // search = (text$: Observable<string>) =>
  //   text$.pipe(
  //     debounceTime(200),
  //     distinctUntilChanged(),
  //     map(term => term.length < 2 ? []
  //       : states.filter(v => v.toLowerCase().indexOf(term.toLowerCase()) > -1).slice(0, 10))
  //   )

  // search = (text$: Observable<string>) =>
  //   text$.pipe(
  //     debounceTime(200),
  //     map(term => term === '' ? []
  //       : statesWithFlags.filter(v => v.name.toLowerCase().indexOf(term.toLowerCase()) > -1).slice(0, 10))
  //   )
}
