import { Component, EventEmitter, ElementRef, HostListener, OnInit, Input, Output, ViewChild, ViewEncapsulation } from '@angular/core';
import { ReportdetailsComponent } from '../reportdetails/reportdetails.component';

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
  constructor() { }

  ngOnInit() {

    var dateObj = new Date();
    this.currentYear = dateObj.getUTCFullYear();
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
