import { Component, OnInit, Input } from '@angular/core';
import { ErrorFieldModel } from '../../../model/error-field.model';

@Component({
  selector: 'app-error-contacts-field',
  templateUrl: './error-contacts-field.component.html',
  styleUrls: ['./error-contacts-field.component.scss']
})
export class ErrorContactsFieldComponent implements OnInit {

  @Input()
  public field: ErrorFieldModel;

  constructor() { }

  ngOnInit() {
  }

}
