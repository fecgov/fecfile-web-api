import { Component, OnInit } from '@angular/core';
import { trigger, transition, style, animate } from '@angular/animations';

@Component({
  selector: 'app-import-done-contacts',
  templateUrl: './import-done-contacts.component.html',
  styleUrls: ['./import-done-contacts.component.scss'],
  animations: [
    trigger('fadeInOut', [
      transition(':enter', [style({ opacity: 0 }), animate(500, style({ opacity: 1 }))]),
      transition(':leave', [animate(0, style({ opacity: 0 }))])
    ])
  ]
})
export class ImportDoneContactsComponent implements OnInit {

  constructor() { }

  ngOnInit() {
  }

}
