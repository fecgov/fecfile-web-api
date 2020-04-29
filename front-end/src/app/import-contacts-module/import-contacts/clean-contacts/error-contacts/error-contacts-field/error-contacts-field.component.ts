import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-error-contacts-field',
  templateUrl: './error-contacts-field.component.html',
  styleUrls: ['./error-contacts-field.component.scss']
})
export class ErrorContactsFieldComponent implements OnInit {

  @Input()
  public field: ErrorContactsFieldComponent;

  constructor() { }

  ngOnInit() {
  }

}
