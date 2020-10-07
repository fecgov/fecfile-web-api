import { Injectable } from '@angular/core';
import {NgbModal} from '@ng-bootstrap/ng-bootstrap';
import {InputModalComponent} from '../../partials/input-modal/input-modal.component';
import {Observable} from 'rxjs';
import {ContactDetailsModalComponent} from '../../../contacts/contact-details-modal/contact-details-modal.component';

@Injectable({
  providedIn: 'root'
})
export class InputDialogService {

  constructor(
      private modalService: NgbModal,
  ) { }

  openFormModal(data: any): Promise<any> {
    const modalRef = this.modalService.open(InputModalComponent);

    modalRef.componentInstance.setContent(data.content);

    modalRef.componentInstance.setSaveAction(data.saveAction);

    modalRef.componentInstance.setViewOnlyFlag(data.viewOnly);

    modalRef.componentInstance.setDialogTitle(data.title);


    return modalRef.result;
  }

  openContactDetails(data: any): Promise<any> {
    const modalRef = this.modalService.open(ContactDetailsModalComponent, {size: 'lg', centered: true, windowClass : 'maxWidthClass'});
    modalRef.componentInstance.setContact(data.contact);
    return modalRef.result;
  }
}
