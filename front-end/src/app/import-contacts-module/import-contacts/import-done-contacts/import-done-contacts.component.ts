import { Component, OnInit, ChangeDetectionStrategy } from '@angular/core';
import { trigger, transition, style, animate } from '@angular/animations';

@Component({
  selector: 'app-import-done-contacts',
  templateUrl: './import-done-contacts.component.html',
  styleUrls: ['./import-done-contacts.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ImportDoneContactsComponent implements OnInit {

  constructor() { }

  ngOnInit() {
  }

}
