import { Component, OnInit } from '@angular/core';
import {NgbActiveModal} from '@ng-bootstrap/ng-bootstrap';
import {ContactModel} from '../model/contacts.model';
import {MessageService} from '../../shared/services/MessageService/message.service';

@Component({
  selector: 'app-contact-details-modal',
  templateUrl: './contact-details-modal.component.html',
  styleUrls: ['./contact-details-modal.component.scss']
})
export class ContactDetailsModalComponent implements OnInit {

  contact: ContactModel;
  constructor(private activeModal: NgbActiveModal,
              private _messageService: MessageService, ) { }
  ngOnInit() {
    this._messageService.sendMessage({cdDisableForm: true});
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
}
