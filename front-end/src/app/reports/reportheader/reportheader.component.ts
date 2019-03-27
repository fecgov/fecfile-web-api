import { Component, EventEmitter, ElementRef, HostListener, OnInit, Input, Output, ViewChild, ViewEncapsulation } from '@angular/core';
import { ReportdetailsComponent } from '../reportdetails/reportdetails.component';
import { FormsService } from '../../shared/services/FormsService/forms.service';

export enum ActiveView {
  transactions = "transactions",
  recycleBin = "recycleBin"
}


//@Output() status: EventEmitter<any> = new EventEmitter<any>();
@Component({
  selector: 'app-reportheader',
  templateUrl: './reportheader.component.html',
  styleUrls: ['./reportheader.component.scss']
})

export class ReportheaderComponent implements OnInit {

public currentYear:number =0;
public reportsView = ActiveView.transactions;
public showSideBar: boolean = false;
  constructor(
    private _formService: FormsService
  ) { }

  ngOnInit() {

    var dateObj = new Date();
    this.currentYear = dateObj.getUTCFullYear();

    if (localStorage.getItem('form3XReportInfo.showDashBoard')==="Y"){
      this._formService.removeFormDashBoard("3X");
    }
  }

  private showFilter() : void {
    if (this.showSideBar){
        this.showSideBar=false;
    } else
    {
      this.showSideBar=true;
    }
  }


  private recycleReports() : void {
    alert("Recycle report is not yet supported");
  }
}
