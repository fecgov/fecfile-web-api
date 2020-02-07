import { Component, EventEmitter, HostListener, Input, OnInit, Output, ViewEncapsulation, OnDestroy } from '@angular/core';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { environment } from '../../../../environments/environment';
import { FormsService } from '../../services/FormsService/forms.service';
import { MessageService } from '../../services/MessageService/message.service';
import { Icommittee_forms } from '../../interfaces/FormsService/FormsService';
import { Subject } from 'rxjs';

@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.scss'],
  encapsulation: ViewEncapsulation.None,
  providers: [NgbTooltipConfig]
})
export class SidebarComponent implements OnInit, OnDestroy {
  

  @Output() status: EventEmitter<any> = new EventEmitter<any>();

  public formType: string = null;
  public iconClass: string = 'close-icon';
  public sidebarVisibleClass: string = 'sidebar-visible';
  public screenWidth: number = 0;
  public tooltipPosition: string = 'right';
  public tooltipLeft: string = 'auto';
  public otherFormsHidden: boolean = true;
  public myFormsHidden: boolean = false;
  public committee_forms: Icommittee_forms[];
  public committee_myforms: Icommittee_forms[];
  public committee_otherforms: Icommittee_forms[];

  private _toggleNavClicked: boolean = false;

  private onDestroy$ = new Subject();

  constructor(
    private _router: Router,
    private _activatedRoute: ActivatedRoute,
    private _formService:FormsService,
    private _config: NgbTooltipConfig
  ) {}

  ngOnInit(): void {
    const route: string = this._router.url;

    this._formService.get_filed_form_types().takeUntil(this.onDestroy$)
     .subscribe(res => this.committee_forms = <Icommittee_forms[]> res);

    this._router
      .events
      .subscribe(val => {
        if(val) {
          if(val instanceof NavigationEnd) {
            if(
              val.url.indexOf('/forms/form/') === 0 ||
              val.url.indexOf('/forms/transactions/') === 0 ||
              val.url.indexOf('/signandSubmit/3X') === 0 ||
              val.url.indexOf('/contacts') === 0 ||
              val.url.indexOf('/addContact') === 0 ||
              val.url.indexOf('/reports') === 0 
             ) {
              this._closeNavBar();
            } else if(
              val.url.indexOf('/dashboard') === 0 ||
              val.url.indexOf('/forms/form/') === -1
            ) {
              this.formType = null;
              this._openNavBar();
            }
          }
        }
      });


    this.screenWidth = window.innerWidth;

    if(this.screenWidth < 768) {
      this.tooltipPosition = 'bottom';
      this.tooltipLeft = '0';
    } else if (this.screenWidth >= 768) {
      this.tooltipPosition = 'right';
      this.tooltipLeft = 'auto';
    }
  }

  ngOnDestroy(): void {
    this.onDestroy$.next(true);
  }
  

  ngDoCheck(): void {
    const route: string = this._router.url;

    if (!this._toggleNavClicked) {
      if(route.indexOf('/forms/form/') === 0 && this.sidebarVisibleClass !== 'sidebar-hidden') {

        let formSelected: string = null;

        this._activatedRoute
          .children[0]
          .params
          .subscribe(param => {
            formSelected = param['form_id'];
            this.formSelected(formSelected);
          });

        this._closeNavBar();

        if(this.formType === null) {
          this.formType = formSelected;
        }
      }
    }
  }

  /**
   * Determines placement of tooltips based on screen size.
   *
   * @class      HostListener (name)
   * @param      {Object}  event   The event
   */
  @HostListener('window:resize', ['$event'])
  onResize(event) {
    this.screenWidth = event.target.innerWidth;

    if(this.screenWidth < 768) {
      this.tooltipPosition = 'bottom';
      this.tooltipLeft = '0';
    } else if (this.screenWidth >= 768) {
      this.tooltipPosition = 'right';
      this.tooltipLeft = 'auto';
    }
  }

  /**
   * Determines which form has been selected.
   *
   * @param      {String}  form    The form
   */
  public formSelected(form: string): void {

    this._router
      .events
      .subscribe(val => {
        if(val instanceof NavigationEnd) {
          if(val.url.indexOf(form) >= 1) {
            if (form !== '3X'){
           // Except Forn3X screens we should not show Form3X related dashboard
              if (localStorage.getItem('form3XReportInfo.showDashBoard')==='Y'){
                this._formService.removeFormDashBoard('3X');
              }
            }
            else if (form === '3X'){
              localStorage.removeItem("form3XReportInfo.dueDate");
              localStorage.removeItem("form3XReportInfo.electionDate");
              localStorage.removeItem("form3XReportInfo.fromDate");
              localStorage.removeItem("form3XReportInfo.regularSpecialReportInd");
              localStorage.removeItem("form3XReportInfo.reportDescription");
              localStorage.removeItem("form3XReportInfo.reportType");
              localStorage.removeItem("form3XReportInfo.toDate");
              localStorage.removeItem("form3xReportTypes");
              localStorage.removeItem("form3xSelectedReportType");
              localStorage.removeItem("form_3X_ReportInfo");
            }

            this.formType = form;
          }
        }
      });
  }

  /**
   * Toggles the sidebar.
   *
   */
  public toggleSideNav(): void {
    this._toggleNavClicked = true;

    if(this.iconClass === 'close-icon') {
      this._closeNavBar();
    } else {
      this._openNavBar();
    }
  }

  /**
   * Toggles weather or not the form navigation is visible.
   *
   * @param      {String}  navType  The navigation type
   */
  public toggleFormNav(navType: string): void {
    if(navType === 'other-forms') {
      this.otherFormsHidden = !this.otherFormsHidden;
    } else if (navType === 'my-forms') {
      this.myFormsHidden = !this.myFormsHidden;
    }
  }

  /**
   * Closes the navbar.
   */
  private _closeNavBar(): void {
    this.iconClass = 'bars-icon';

    setTimeout(() => {
      this.sidebarVisibleClass = 'sidebar-hidden';
    }, 100);

    this.status.emit({
      showSidebar: false
    });
  }

  /**
   * Opens the navbar.
   */
  private _openNavBar(): void {
    this.iconClass = 'close-icon';

    setTimeout(() => {
      this.sidebarVisibleClass = 'sidebar-visible';
    }, 100);

    this.status.emit({
      showSidebar: true
    });
  }
}
