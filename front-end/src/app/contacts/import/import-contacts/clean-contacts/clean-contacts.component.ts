import { Component, OnInit } from '@angular/core';
import { trigger, transition, style, animate } from '@angular/animations';

@Component({
  selector: 'app-clean-contacts',
  templateUrl: './clean-contacts.component.html',
  styleUrls: ['./clean-contacts.component.scss'],
  animations: [
    trigger('fadeInOut', [
      transition(':enter', [style({ opacity: 0 }), animate(500, style({ opacity: 1 }))]),
      transition(':leave', [animate(0, style({ opacity: 0 }))])
    ])
  ]
})
export class CleanContactsComponent implements OnInit {

  constructor() { }

  ngOnInit() {
  }

}
