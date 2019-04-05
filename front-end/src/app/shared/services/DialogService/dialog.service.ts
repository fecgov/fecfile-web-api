import { Injectable, ViewChild } from '@angular/core';
import { Observable, of } from 'rxjs';
import { NgbModal, ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';
import { ModalHeaderClassEnum } from '../../partials/confirm-modal/confirm-modal.component';

@Injectable({
  providedIn: 'root'
})
export class DialogService {

  @ViewChild('content') modalContent;

  constructor(
    private _modalService: NgbModal
  ) { }

  public confirm(message?: string,
                  modalContent?: any,
                  modalTitle?: string,
                  isShowCancel?: boolean,
                  headerClass?: ModalHeaderClassEnum): Promise<any> {
    const modalOptions: any = {
      'backdrop': true,
      'keyboard': false,
    };

    const modalRef = this._modalService
      .open(modalContent, modalOptions);

    if (message) {
      modalRef.componentInstance.message = message;
    }
    if (modalTitle) {
      modalRef.componentInstance.modalTitle = modalTitle;
    }
    if (isShowCancel !== undefined && isShowCancel !== null) {
      modalRef.componentInstance.isShowCancel = isShowCancel;
    }
    if (headerClass) {
      modalRef.componentInstance.headerClass = headerClass;
    }
    return modalRef
      .result
      .then(res => {
        /**
         * Returned if a button on the modal is clicked.
         */
        return res;
      }, (res) => {
        /**
         * Returned if the modal backdrop or escape is clicked.
         * Although in this case I have the keyboard disabled.
         */
        if (res === ModalDismissReasons.BACKDROP_CLICK || res === ModalDismissReasons.ESC) {
          return 'cancel';
        }
      });
  }
  

  public reportExist(message?: string,
    modalContent?: any,
    modalTitle?: string,
    isShowCancel?: boolean,
    isShowReportExist?: boolean,
    headerClass?: ModalHeaderClassEnum): Promise<any> {
    const modalOptions: any = {
    'backdrop': true,
    'keyboard': false,
    };

    const modalRef = this._modalService
    .open(modalContent, modalOptions);

    if (message) {
      modalRef.componentInstance.message = message;
    }
    if (modalTitle) {
      modalRef.componentInstance.modalTitle = modalTitle;
    }
    if (isShowCancel !== undefined && isShowCancel !== null) {
      modalRef.componentInstance.isShowCancel = isShowCancel;
    }
    if (isShowReportExist !== undefined && isShowReportExist !== null) {
      modalRef.componentInstance.isShowReportExist = isShowReportExist;
    }
    if (headerClass) {
      modalRef.componentInstance.headerClass = headerClass;
    }
    return modalRef
      .result
      .then(res => {
      /**
      * Returned if a button on the modal is clicked.
      */
        return res;
        }, (res) => {
      /**
      * Returned if the modal backdrop or escape is clicked.
      * Although in this case I have the keyboard disabled.
      */
      if (res === ModalDismissReasons.BACKDROP_CLICK || res === ModalDismissReasons.ESC) {
        return 'cancel';
        }
      });
    }

}
