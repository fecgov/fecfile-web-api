import { Component, ViewEncapsulation, OnInit } from '@angular/core';
import { NgbModal, ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';
import { AuthService } from '../../services/AuthService/auth.service';

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class HeaderComponent implements OnInit {

  public closeResult: string;

  constructor(
    private _authService: AuthService,
    private _modalService: NgbModal
  ) { }

  ngOnInit() {}

  /**
   * Open's the legal disclaimer modal dialog.
   *
   * @param      {Object}  content  The content
   */
  public open(content): void {
    this._modalService.open(content, {ariaLabelledBy: 'modal-basic-title'}).result.then((result) => {
      this.closeResult = `Closed with: ${result}`;
    }, (reason) => {
      this.closeResult = `Dismissed ${this._getDismissReason(reason)}`;
    });
  }

  /**
   * Gets the dismiss reason.
   *
   * @param      {Any}  reason  The reason
   * @return     {<type>}  The dismiss reason.
   */
  private _getDismissReason(reason: any): string {
    if (reason === ModalDismissReasons.ESC) {
      return 'by pressing ESC';
    } else if (reason === ModalDismissReasons.BACKDROP_CLICK) {
      return 'by clicking on a backdrop';
    } else {
      return  `with: ${reason}`;
    }
  }

  /**
   * Logs a user out.
   *
   */
  public logout(): void {
    this._authService.doSignOut();
  }
}
