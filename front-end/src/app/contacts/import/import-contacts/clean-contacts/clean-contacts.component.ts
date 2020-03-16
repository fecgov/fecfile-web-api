import { Component, OnInit } from '@angular/core';
import { trigger, transition, style, animate } from '@angular/animations';
import { ContactModel } from 'src/app/contacts/model/contacts.model';
import { ImportContactsService } from '../service/import-contacts.service';

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

  // public contacts: Array<ContactModel>;
  public contacts: Array<any>;

  constructor(private importContactsService: ImportContactsService) { }

  ngOnInit() {
    this.getContacts();
  }

  public getContacts() {
    this.importContactsService.getDuplicates().subscribe((res: any) => {
      this.contacts = res;
    });
  }

}
