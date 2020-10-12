import { ReportsService } from './../reports/service/report.service';
import { AuthService } from './../shared/services/AuthService/auth.service';
import { Component, OnInit, ViewChild, ViewEncapsulation } from '@angular/core';
import { NgbModal, ModalDismissReasons } from '@ng-bootstrap/ng-bootstrap';
import { SessionService } from '../shared/services/SessionService/session.service';
import { ApiService } from '../shared/services/APIService/api.service';
import { MessageService } from '../shared/services/MessageService/message.service';
import { HeaderComponent } from '../shared/partials/header/header.component';
import { SidebarComponent } from '../shared/partials/sidebar/sidebar.component';
import { FormsComponent } from '../forms/forms.component';
import { FormsService } from '../shared/services/FormsService/forms.service';
import { of } from 'rxjs';



@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class DashboardComponent implements OnInit {

  @ViewChild('content') content: any;
  
  public showSideBar: boolean = true;
  public showLegalDisclaimer: boolean = false;
  public closeResult: string;
  modalRef: any;

  upcomingReportsList: any = null;
  upcomingReportsListError = false;
  upcomingReportsListEmpty = false;
  recentlySavedReports: any;
  recentlySavedReportsError = false;
  recentlySavedReportsEmpty = false;
  recentlySubmittedReports: any;
  recentlySubmittedReportsError = false;
  recentlySubmittedReportsEmpty = false;

  constructor(
    private _sessionService: SessionService,
    private _apiService: ApiService,
    private _modalService: NgbModal,
    private _messageService: MessageService,
    private _formService: FormsService,
    private modalService: NgbModal, 
    private _authService: AuthService, 
    private _reportService: ReportsService

  ) { }

  ngOnInit(): void {
    if (localStorage.getItem('form3XReportInfo.showDashBoard')==="Y"){
       this._formService.removeFormDashBoard("3X");
    }
    this._showFirstTimeCOHIfAppliable();
    this._populateUpcomingReportsList();
    this._populateRecentlySavedReportsList();
    this._populateRecentlySubmittedReportsList();
  }
  
  private _populateRecentlySubmittedReportsList() {
    //reset flags first
    this.recentlySubmittedReportsEmpty = false;
    this.recentlySubmittedReportsError = false;

    this._reportService.getRecentlySubmittedReports().subscribe((res:any)=>{
      if(res){
        if(res.length > 0){
          this.recentlySubmittedReports = res;
        }else{
          this.recentlySubmittedReportsEmpty = true;
        }
      }
    }, error => {
      if(error){
        this.recentlySubmittedReportsError = true;
      }
    });
  }

  
  private _populateRecentlySavedReportsList() {
    //reset flags first
    this.recentlySavedReportsEmpty = false;
    this.recentlySavedReportsError = false;

    this._reportService.getRecentlySavedReports().subscribe((res:any)=>{
      if(res){
        if(res.length > 0){
          this.recentlySavedReports = res;
        }else{
          this.recentlySavedReportsEmpty = true;
        }
      }
    } , error => {
        if(error){
          this.recentlySavedReportsError = true;
        }
    });
  }
  
  
  private _populateUpcomingReportsList() {
    //reset flags first
    this.upcomingReportsListEmpty = false;
    this.upcomingReportsListError = false;

    this._reportService.getUpcomingReports().subscribe((res:any)=>{
      if(res){
        if(res.length > 0){
          this.upcomingReportsList = res;
        }else{
          this.upcomingReportsListEmpty = true;
        }
      }
    }, error => {
      if(error){
        this.upcomingReportsListError = true;
      }
    });
  }
  
  
  
  private _showFirstTimeCOHIfAppliable() {
    if(this._authService.isCommitteeAdmin() || this._authService.isBackupCommitteeAdmin() || this._authService.isAdmin()){
      this._apiService.getCashOnHandInfoStatus().subscribe(res => {
        if(res && res.showMessage){
          this.openModal();
        }
      });
    }
  }

  public openCOHInfoModal(content) {
    this.modalRef = this.modalService.open(content, { size: 'lg', centered: true, windowClass: 'custom-class' });
  }

  public openModal() {
    // if (this.loggedInUserRole === Roles.Editor || this.loggedInUserRole === Roles.Reviewer) {
      // this._authService.showPermissionDeniedMessage();
    // } else {
      this.openCOHInfoModal(this.content);
    // }
  }



  /**
   * Show's or hides the sidebar navigation.
   */
  public toggleSideNav(): void {
    if (this.showSideBar) {
      this.showSideBar = false;
    } else if (!this.showSideBar) {
      this.showSideBar = true;
    }
  }

  /**
   * Logs a user out.
   */
  public logout(): void {
    this._sessionService.destroy();
  }

  /**
   * Open's the legal disclaimer modal dialog.
   *
   * @param      {Object}  content  The content
   */
  public open(): void {
    this.showLegalDisclaimer = !this.showLegalDisclaimer;
    /*this._modalService.open(content, {ariaLabelledBy: 'modal-basic-title'}).result.then((result) => {
      this.closeResult = `Closed with: ${result}`;
    }, (reason) => {
      this.closeResult = `Dismissed ${this._getDismissReason(reason)}`;
    });*/
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

}
