import { Injectable, ViewChild } from '@angular/core';
import { Observable, of } from 'rxjs';
import { NgbModal, ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';

@Injectable({
  providedIn: 'root'
})
export class DialogService {

	@ViewChild('content') modalContent;

  constructor(
  	private _modalService: NgbModal
  ) { }

  public confirm(message?: string, modalContent?: any): Promise<any> {
    let modalOptions: any = {
    	'backdrop': true,
    	'keyboard': false,
    };
		
    const modalRef = this._modalService
    	.open(modalContent, modalOptions);		
			modalRef.componentInstance.message = message;
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
					if(res === ModalDismissReasons.BACKDROP_CLICK || res === ModalDismissReasons.ESC) {
						return 'cancel';
					}
				});
  }
}
