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
    // const confirmation = window.confirm(message || 'Are you sure?');
    let result: boolean = true;
    
    return this._modalService
    	.open(modalContent)
    	.result;
   // console.log('this._modalService.open(modalContent).result: ', );

	/*this._modalService.open(modalContent)
		.result
		.then(res => {
			console.log('this.getDismissReason(res): ', this.getDismissReason(res));
			if(this.getDismissReason(res) === 'okay') {
				result = true;
			} else if(this.getDismissReason(res) === 'cancel') {
				result = false;
			}			
		});*/

	//console.log('result: ', result);
  }

  private getDismissReason(reason: any): string {
    if (reason === ModalDismissReasons.ESC) {
      return 'by pressing ESC';
    } else if (reason === ModalDismissReasons.BACKDROP_CLICK) {
      return 'by clicking on a backdrop';
    } else {
      return  reason;
    }
  }  
}
