import { Component, HostBinding, Input, OnDestroy, OnInit, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { ModalDismissReasons, NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { Subject } from 'rxjs';
import { Subscription } from 'rxjs/Subscription';
import { ApiService } from '../shared/services/APIService/api.service';
import { AuthService } from '../shared/services/AuthService/auth.service';
import { MessageService } from '../shared/services/MessageService/message.service';
import { SessionService } from '../shared/services/SessionService/session.service';
import { UtilService } from '../shared/utils/util.service';
import { ReportsService } from './../reports/service/report.service';
import { DatePipe } from '@angular/common';

@Component({
  selector: 'app-app-layout',
  templateUrl: './app-layout.component.html',
  styleUrls: ['./app-layout.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class AppLayoutComponent implements OnInit, OnDestroy {
  
  ngOnDestroy(): void {
      this.onDestroy$.next(true);
      this.subscription.unsubscribe();
  }

  @HostBinding('@.disabled')
  public animationsDisabled = true;
  
  @Input() status: any;

  public committeeName: string = null;
  public committeeId: string = null;
  public closeResult: string = null;
  public dashboardClass: string = null;
  public formDueDate: number = null;
  public formDescription: string = null;
  public reportType: string = null;
  public formType: string = null;
  public formStartDate: string = null;
  public formEndDate: string = null;
  public formDaysUntilDue: string = null;
  public radAnalystInfo: any = {};
  public showLegalDisclaimer: boolean = false;
  public showFormDueDate: boolean = false;
  public showSideBar: boolean = true;
  public sideBarClass: string = null;
  public toggleMenu: boolean = false;
  public dueDate: string = null;
  public reportOverDue: boolean = false;
  private subscription: Subscription;
  public currentReportData:any = {};
  public electionDate: string = null;
  public electionState: string = null;
  public semiAnnualStartDate: string;
  public semiAnnualEndDate: string;
  private _step: string = null;

  private _datePipe: DatePipe;
  private onDestroy$ = new Subject();

  constructor(
    private _apiService: ApiService,
    private _sessionService: SessionService,
    private _messageService: MessageService,
    private _utilService: UtilService,
    public _router: Router,
    private _modalService: NgbModal,
    public _activatedRoute: ActivatedRoute,
    public _authService: AuthService,
    public _reportService: ReportsService
  ) {
    this._datePipe = new DatePipe('en-US');
  }

  ngOnInit(): void {
    let route: string = this._router.url;

    this._apiService.getCommiteeDetails().takeUntil(this.onDestroy$).subscribe(res => {
      if (res) {
        localStorage.setItem('committee_details', JSON.stringify(res));

        this.committeeName = res.committeename;
        this.committeeId = res.committeeid;
        this._messageService.sendMessage({ committee_details_loaded: true });
      }
    });

    this._apiService.getRadAnalyst().takeUntil(this.onDestroy$).subscribe(res => {
      if (res) {
        if (Array.isArray(res.response)) {
          this.radAnalystInfo = res.response[0];
        }
      }
    });

    this.subscription = this._router.events.takeUntil(this.onDestroy$).subscribe(val => {
      if (val instanceof NavigationEnd) {
        if (this.toggleMenu) {
          this.toggleMenu = false;
        }
        if (val.url.indexOf('/signandSubmit') === 0) {
          if (this.toggleMenu) {
            this.showSideBar = true;
            this.sideBarClass = 'app-container dashboard active';
          } else {
            this.showSideBar = false;
            this.sideBarClass = 'app-container active';
          }
        } else if (val.url.indexOf('/dashboard') === 0) {
          if (this.toggleMenu) {
            this.showSideBar = true;
            this.sideBarClass = 'app-container dashboard active';
          } else {
            this.showSideBar = false;
            this.sideBarClass = 'app-container active';
          }
          this._utilService.removeLocalItems('form_', 5);
        } else if (val.url.indexOf('/forms') === 0) {
          if (this.toggleMenu) {
            this.showSideBar = true;
            this.sideBarClass = 'app-container active';
          }
        } else if (val.url.indexOf('/forms') !== 0 || val.url.indexOf('/dashboard') !== 0) {
          this._utilService.removeLocalItems('form_', 5);
        }
      }
    });

    this._messageService.getMessage().takeUntil(this.onDestroy$).subscribe(message=>{
      if(message && message.action === 'updateCurrentReportHeaderData' && message.data){
        this.currentReportData = message.data;
        this.populateHeaderData(this.currentReportData);
      }
      else if(message && message.action === 'updateHeaderInfo' && message.data){
        this.formType = message.data.formType;
      }
    });

  }

  ngDoCheck(): void {
    const route: string = this._router.url;
    
    let formType = this.extractFormType();
    // to refresh/clear Dash Board Filter options
    localStorage.removeItem('reports.filters');
    localStorage.removeItem('notifications.filters');
    localStorage.removeItem('Reports.view');

    this._step = this._activatedRoute.snapshot.queryParams.step;
    let formInfo: any = '';
    if (route === '/dashboard') {
      /**
       * Fix this issue with the sidenar on the dashboard.
       * This causes the sidebar to always show, even if the hide button is clicked.
       */

      this.sideBarClass = 'dashboard active';
      this.showFormDueDate = false;
    } else if (route === '/reports') {
      this.showFormDueDate = false;
    } else if (formType && (
      route.indexOf(`/forms/form/${formType}`) === 0  ||
      route.indexOf(`/forms/transactions/${formType}`) === 0 ||
      route.indexOf('/signandSubmit') === 0)
    ) {
      if (localStorage.getItem(`form_${formType}_report_type`) !== null) {
        formInfo = JSON.parse(localStorage.getItem(`form_${formType}_report_type`));
      } else if (localStorage.getItem(`form_${formType}_report_type_backup`) !== null) {
        formInfo = JSON.parse(localStorage.getItem(`form_${formType}_report_type_backup`));
      }


      if (typeof formInfo === 'object') {
        if(this.currentReportData && Array.isArray(this.currentReportData) && this.currentReportData.length > 0){
          this.populateHeaderData(this.currentReportData[0]);
        }
        /* else{
          this.populateHeaderData(formInfo);
        } */

        if (this._step !== 'step_1') {
          this.showFormDueDate = true;
        } else {
          this.showFormDueDate = false;
        }
      } else {
        this.showFormDueDate = false;
      }
    }
  }
  
  private extractFormType() {
    let formType = null;
    if (this.formType) {
      if (this.formType.length === 3) {
        formType = this.formType.substr(1, 3);
      }
      else if (this.formType.length === 2) {
        formType = this.formType;
      }
    }
    else if(this.currentReportData && this.currentReportData.formtype){
      formType = this.currentReportData.formtype;
      if (formType.length === 3) {
        formType = formType.substr(1, 3);
      }
    }
    return formType;
  }

  private populateHeaderData(formInfo: any) {
    if (formInfo.hasOwnProperty('formType')) {
      this.formType = formInfo.formType;
    }
    else if (formInfo.hasOwnProperty('formtype')) {
      this.formType = formInfo.formtype;
    }
    if (formInfo.hasOwnProperty('report_type_desciption')) {
      this.formDescription = formInfo.report_type_desciption;
    }
    else if (formInfo.hasOwnProperty('reporttypedescription')) {
      this.formDescription = formInfo.reporttypedescription;
    }
    if (formInfo.hasOwnProperty('report_type')) {
      this.reportType = formInfo.report_type;
    }
    else if (formInfo.hasOwnProperty('reporttype')) {
      this.reportType = formInfo.reporttype;
    }
    if (formInfo.hasOwnProperty('cvgStartDate')) {
      this.formStartDate = this._utilService.formatDateToYYYYMMDD(formInfo.cvgStartDate);
    }
    else if (formInfo.hasOwnProperty('cvgstartdate')) {
      this.formStartDate = this._utilService.formatDateToYYYYMMDD(formInfo.cvgstartdate);
    }
    if (formInfo.hasOwnProperty('cvgEndDate')) {
      this.formEndDate = this._utilService.formatDateToYYYYMMDD(formInfo.cvgEndDate);
    }
    else if (formInfo.hasOwnProperty('cvgenddate')) {
      this.formEndDate = this._utilService.formatDateToYYYYMMDD(formInfo.cvgenddate);
    }
    if (formInfo.hasOwnProperty('daysUntilDue')) {
      this.formDaysUntilDue = Math.abs(formInfo.daysUntilDue).toString();
    }
    else if (formInfo.hasOwnProperty('daysuntildue')) {
      this.formDaysUntilDue = Math.abs(formInfo.daysuntildue).toString();
    }
    if (formInfo.hasOwnProperty('dueDate')) {
      this.dueDate = formInfo.dueDate;
    }
    else if (formInfo.hasOwnProperty('duedate')) {
      this.dueDate = formInfo.duedate;
    }
    if (formInfo.hasOwnProperty('overDue')) {
      this.reportOverDue = formInfo.overDue;
    }
    else if (formInfo.hasOwnProperty('overdue')) {
      /*if (formInfo.overdue > 0) {
            this.reportOverDue = true;
          }*/
      // //console.log("formInfo.overdue =", formInfo.overdue);
      this.reportOverDue = formInfo.overdue;
    }
    if(formInfo.hasOwnProperty('election_date')){
      this.electionDate = formInfo.election_date;
    }
    else if(formInfo.hasOwnProperty('electiondate')){
      this.electionDate = formInfo.electiondate;
    }
    if(formInfo.hasOwnProperty('election_state')){
      this.electionState = formInfo.election_state;
    }
    else if(formInfo.hasOwnProperty('electionstate')){
      this.electionState = formInfo.electionstate;
    }

    if(formInfo.hasOwnProperty('semi_annual_start_date')){
      this.semiAnnualStartDate = formInfo.semi_annual_start_date;
    }

    if(formInfo.hasOwnProperty('semi_annual_end_date')){
      this.semiAnnualEndDate = formInfo.semi_annual_end_date;
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

    if (this.showSideBar) {
      if (route) {
        if (route.indexOf('/dashboard') === 0) {
          this.sideBarClass = 'dashboard active';
        } else if (route.indexOf('/dashboard') === -1) {
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
  public open(content): void {
    this._modalService.open(content, { ariaLabelledBy: 'modal-basic-title' }).result.then(
      result => {
        this.closeResult = `Closed with: ${result}`;
      },
      reason => {
        this.closeResult = `Dismissed ${this._getDismissReason(reason)}`;
      }
    );
  }

  private _getDismissReason(reason: any): string {
    if (reason === ModalDismissReasons.ESC) {
      return 'by pressing ESC';
    } else if (reason === ModalDismissReasons.BACKDROP_CLICK) {
      return 'by clicking on a backdrop';
    } else {
      return `with: ${reason}`;
    }
  }

  public editFrom(): void {
    
    let formType :string = this.extractFormType();
    this._reportService.getReportInfo(formType, this._activatedRoute.snapshot.queryParams.reportId).subscribe(res => {
      
      let queryParamsMap: any = {
        step: 'step_1',
        edit: true,
        reportId: this._activatedRoute.snapshot.queryParams.reportId
      };
  
      this._router.navigate([`/forms/form/${formType}`], {
        queryParams: queryParamsMap
      });
  
      res = res[0];
      this._messageService.sendUpdateReportTypeMessage({
        currentReportData: {
          
          'currentReportDescription': res.reporttypedescription,
          'currentStartDate': res.cvgStartDate ? this._datePipe.transform(res.cvgStartDate, 'yyyy-MM-dd') : null, 
          'currentEndDate': res.cvgEndDate ? this._datePipe.transform(res.cvgEndDate, 'yyyy-MM-dd') : null,
          'currentDueDate' : res.duedate,
          'currentReportType': res.reporttype,
          'currentElectionDate':res.election_date ? res.election_date : res.electiondate,
          'currentElectionState':res.election_state ? res.election_state : res.electionstate,
          'currentSemiAnnualStartDate': res.semi_annual_start_date,
          'currentSemiAnnualEndDate': res.semi_annual_end_date
        }
      });
    })
    
  }
}
