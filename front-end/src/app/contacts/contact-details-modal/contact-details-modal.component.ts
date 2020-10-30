import { Component, OnInit } from '@angular/core';
import {NgbActiveModal} from '@ng-bootstrap/ng-bootstrap';
import {ContactModel} from '../model/contacts.model';
import {MessageService} from '../../shared/services/MessageService/message.service';
import {ContactsService} from '../service/contacts.service';

@Component({
  selector: 'app-contact-details-modal',
  templateUrl: './contact-details-modal.component.html',
  styleUrls: ['./contact-details-modal.component.scss']
})
export class ContactDetailsModalComponent implements OnInit {

  contact: ContactModel;
  showResponse: boolean = false;
  responseMessage: string = '';
  notesValue: string = '';
  constructor(private activeModal: NgbActiveModal,
              private _messageService: MessageService,
              private _contactService: ContactsService,
              ) { }
  ngOnInit() {
    this._messageService.sendMessage({cdDisableForm: true});
    this._contactService.getContactDetails(this.contact.id).subscribe( res => {
      if (res && res.length >= 1 && res !== undefined) {
        this.contact.setTransactions(res);
      } else {
        this.contact.setTransactions(null);
      }
    });
  }

  decline() {
    this.activeModal.close('close');
  }

  agree() {
    this.activeModal.close('agree');
  }

  editContact() {
    this._messageService.sendMessage({cdEnableForm: true});
  }
  setContact(value: ContactModel) {
    this.contact = value;
  }

    saveNotes() {
      this._contactService.updateNotes(this.contact.id, this.notesValue).subscribe( res => {
        if (res) {
          this.showResponse = true;
          this.responseMessage = 'Successfully Updated Notes';
          setTimeout(() => {
            this.showResponse = false;
            this.responseMessage = '';
          }, 3000);
        }
      });
    }
}
