import { Component, HostListener, Input, OnInit, ViewEncapsulation } from '@angular/core';
import { NavigationEnd, Router } from '@angular/router';
import { NgbModal, ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';
import { SessionService } from '../shared/services/SessionService/session.service';
import { MessageService } from '../shared/services/MessageService/message.service';
import { ApiService } from '../shared/services/APIService/api.service';
import { HeaderComponent } from '../shared/partials/header/header.component';
import { SidebarComponent } from '../shared/partials/sidebar/sidebar.component';
import { FormsComponent } from '../forms/forms.component';

@Component({
  selector: 'app-app-layout',
  templateUrl: './app-layout.component.html',
  styleUrls: ['./app-layout.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class AppLayoutComponent implements OnInit {

  @Input() status: any;

  public committeeName: string = null;
  public committeeId: string = null;
  public closeResult: string = null;
  public dashboardClass: string = null;
  public formDueDate: number = null;
  public formDescription: string = null;
  public formType: string = null;
  public formStartDate: string = null;
  public formEndDate: string = null;
  public radAnalystInfo: any = {};
  public showLegalDisclaimer: boolean = false;
  public showFormDueDate: boolean = false
  public showSideBar: boolean = true;
  public sideBarClass: string = null;
  public toggleMenu: boolean = false;

	constructor(
    private _apiService: ApiService,
		private _sessionService: SessionService,
    private _messageService: MessageService,
    private _router: Router,
    private _modalService: NgbModal
	) { }

	ngOnInit(): void {
    let route: string = this._router.url;

    this._apiService
      .getCommiteeDetails()
      .subscribe(res => {
        if(res) {
          localStorage.setItem('committee_details', JSON.stringify(res));

          this.committeeName = res.committeename;
          this.committeeId = res.committeeid;
          this._messageService
            .sendMessage({'committee_details_loaded': true});
        }
      });

    this._apiService
      .getRadAnalyst()
      .subscribe(res => {
        if (res) {
          if (Array.isArray(res.response)) {
            this.radAnalystInfo = res.response[0];
          }
        }
      });

    this._router
      .events
      .subscribe(val => {
        if(val instanceof NavigationEnd) {
          if(this.toggleMenu) {
            this.toggleMenu = false;
          }
          if(val.url.indexOf('/dashboard') === 0) {
            this.sideBarClass = 'dashboard active';
            this.showSideBar = true;
          } else if(val.url.indexOf('/forms') === 0) {
            if(this.toggleMenu) {
              this.showSideBar = true;
              this.sideBarClass = 'active';
            }
          }
        }
      });
  }

  /**
   * TODO: Figure out why this was placed here.
   */
  // @HostListener('window:beforeunload', ['$event'])
  // unloadNotification($event: any) {
  //   localStorage.clear();
  // }

  ngDoCheck(): void {
    const route: string = this._router.url;

    if (route === '/dashboard') {
      this.sideBarClass = 'dashboard active';
      this.showFormDueDate = false;
    } else if (route.indexOf('/forms/form/3X') === 0) {
      if (localStorage.getItem('form_3X_report_type') !== null) {
        const formInfo: any = JSON.parse(localStorage.getItem('form_3X_report_type'));
        const dueDate: any = new Date(formInfo.dueDate);
        const oneDay: number = 24*60*60*1000;
        const today: any = new Date();

        this.showFormDueDate = true;
        this.formType = formInfo.formType;
        this.formDueDate = Math.round(Math.abs((today.getTime() - dueDate.getTime())/(oneDay)));
        this.formDescription = formInfo.reportTypeDescription;
        this.formStartDate = formInfo.cvgStartDate;
        this.formEndDate = formInfo.cvgEndDate;
      }
    } else {
        this.showFormDueDate = false;
    }
  }
  /**
   * Shows the top nav in tablet and mobile phone view when clicked.
   */
  public toggleTopNav(): void {
    this.toggleMenu = !this.toggleMenu;
  }

  /**
   * Logs a user out.
   */
  public logout(): void {
    this._sessionService.destroy();
  }

  /**
   * Get's message from child components.
   *
   * @param      {Object}  e       The event object.
   */
  public onNotify(e): void {
    const route: string = this._router.url;
    this.showSideBar = e.showSidebar;

    if(this.showSideBar) {
      if(route) {
        if(route.indexOf('/dashboard') === 0) {
          this.sideBarClass = 'dashboard active';
        } else if(route.indexOf('/dashboard') === -1) {
          this.sideBarClass = 'active';
        }
      }
    } else {
      this.sideBarClass = '';
    }
  }

  /**
   * Opens the modal dialog.
   *
   * @param      {Object}  content  The content
   */
  public open(content): void{
    this._modalService
      .open(content, {ariaLabelledBy: 'modal-basic-title'})
      .result
      .then((result) => {
        this.closeResult = `Closed with: ${result}`;
    }, (reason) => {
      this.closeResult = `Dismissed ${this._getDismissReason(reason)}`;
    });
  }

  private _getDismissReason(reason: any): string {
    if (reason === ModalDismissReasons.ESC) {
      return 'by pressing ESC';
    } else if (reason === ModalDismissReasons.BACKDROP_CLICK) {
      return 'by clicking on a backdrop';
    } else {
      return  `with: ${reason}`;
    }
  }
}
