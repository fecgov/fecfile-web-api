import { Component, OnInit, NgZone, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Observable, of } from 'rxjs';
import { NgbModal, ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';
import { environment } from '../../environments/environment';
import { MessageService } from '../shared/services/MessageService/message.service';
import { ValidateComponent } from '../shared/partials/validate/validate.component';

@Component({
  selector: 'app-forms',
  templateUrl: './forms.component.html',
  styleUrls: ['./forms.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class FormsComponent implements OnInit {

	public form_type: string = '';
  public closeResult: string = '';
  public canContinue: boolean = false;
  public showValidateBar: boolean = false;

  constructor(
  	private _activeRoute: ActivatedRoute,
    private _modalService: NgbModal,
    private _ngZone: NgZone,
    private _messageService: MessageService
  ) { }

  ngOnInit(): void {
  	this._activeRoute
      .params
      .subscribe( params => {
  		  this.form_type = params.form_id;
  	});

    this._messageService
      .getMessage()
      .subscribe(res => {
        if(res.validateMessage) {
          this.showValidateBar = res.validateMessage.showValidateBar;
        }
      });
  }

  /**
   * Open's the modal window.
   *
   * @param      {Object}  content  The content
   */
  public openModal(content): void {
    this._modalService.open(content, {ariaLabelledBy: 'modal-basic-title'}).result.then((result) => {
      this.closeResult = `Closed with: ${result}`;
    }, (reason) => {
      this.closeResult = `Dismissed ${this._getModalDismissReason(reason)}`;
    });
  }

  /**
   * Gets the dismiss reason.
   *
   * @param      {Any}  reason  The reason
   * @return     {<type>}  The dismiss reason.
   */
  private _getModalDismissReason(reason: any): string {
    if (reason === ModalDismissReasons.ESC) {
      return 'by pressing ESC';
    } else if (reason === ModalDismissReasons.BACKDROP_CLICK) {
      return 'by clicking on a backdrop';
    } else {
      return  `with: ${reason}`;
    }
  }
}
