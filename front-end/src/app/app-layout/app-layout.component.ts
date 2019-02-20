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

	public showSideBar: boolean = true;
  public sideBarClass: string = 'dashboard active';
  public toggleMenu: boolean = false;
  public committeeName: string = '';
  public committeeId: string = '';
  public closeResult: string = '';
  public dashboardClass: string = '';
  public showLegalDisclaimer: boolean = false;
  public showForm3XDashBoard: boolean = false;
  public form3XReportDashBoardLine1 = '';
  public form3XReportDashBoardLine2 = '';
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

    this._router
      .events
      .subscribe(val => {
        if(val instanceof NavigationEnd) {
          if(this.toggleMenu) {
            this.toggleMenu = false;
          }
          if(
            val.url.indexOf('/dashboard') === 0 ||
            val.url.indexOf('/reports') === 0
          ) {
            this.sideBarClass = 'dashboard active';
          } else if(val.url.indexOf('/forms') === 0) {
            if(this.toggleMenu) {
              this.sideBarClass = 'visible';
            } else {
              this.sideBarClass = '';
            }
          }
        }
      });
  }

  ngDoCheck(): void {
    let route: string = this._router.url;

    if(localStorage.getItem('form3XReportInfo.showDashBoard') !== null &&  localStorage.getItem('form3XReportInfo.showDashBoard') !== ""){
      this.showForm3XDashBoard = true;
      this.form3XReportDashBoardLine1 = localStorage.getItem('form3XReportInfo.DashBoardLine1');
      this.form3XReportDashBoardLine2 = localStorage.getItem('form3XReportInfo.DashBoardLine2');

    }
  }

  @HostListener('window:beforeunload', ['$event'])
  unloadNotification($event: any) {
    localStorage.clear();
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
    let route: string = this._router.url;
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
