import { NgForm } from '@angular/forms';
import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs';
import 'rxjs/add/observable/of';
import { environment } from '../../../../environments/environment';
import { CookieService } from 'ngx-cookie-service';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-sched-h1',
  templateUrl: './sched-h1.component.html',
  styleUrls: ['./sched-h1.component.scss']
})


export class SchedH1Component implements OnInit { 
  public formType = '';

  constructor(
    private _http: HttpClient,
    private _activatedRoute: ActivatedRoute,
    private _cookieService: CookieService,
  ) { }

  ngOnInit() {
    // localStorage.setItem('cmte_type_category', 'PAC')
    //console.log(localStorage.getItem('cmte_type_category'));
    this.formType = this._activatedRoute.snapshot.paramMap.get('form_id');

  }

  isPac() {
    //console.log(localStorage.getItem('cmte_type_category'));
    // return true;

    const cmteDetails = JSON.parse(localStorage.getItem(`committee_details`));    
    //return localStorage.getItem('cmte_type_category') === 'PAC';
    return cmteDetails.cmte_type_category === 'PAC';
  }

  saveH1(f: NgForm) {
    const token: string = JSON.parse(this._cookieService.get('user'));
    const url: string = `${environment.apiUrl}/sh1/schedH1`;
    // const data: any = JSON.stringify(receipt);
    let httpOptions = new HttpHeaders();

    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
    httpOptions = httpOptions.append('Content-Type', 'application/json');
    console.log('post h1 url:' + url);

    // build form data and adding report_id
    const formData: FormData = new FormData();
    // formData = new FormData() 
    let h1_obj = { "transaction_type_identifier": "ALLOC_H1" };
    // set report_id
    h1_obj['report_id'] = '0'

    let reportType: any = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type`));
    if (reportType === null || typeof reportType === 'undefined') {
      reportType = JSON.parse(localStorage.getItem(`form_${this.formType}_report_type_backup`));
    }
    console.log(reportType);
    if (reportType.hasOwnProperty('reportId')) {
      h1_obj['reprot_id'] = reportType.reportId;
      // formData.append('report_id', reportType.reportId);
    } else if (reportType.hasOwnProperty('reportid')) {
      // formData.append('report_id', reportType.reportid);
      h1_obj['report_id'] = reportType.reportid;
    }
    console.log(reportType.reportid)
    // formData.append('federal_percent', '0.45');
    // formData.append('non_federal_percent', '0.55');
    // h1_obj['report_id'] = '121';
    
    if (this.isPac()) {
      h1_obj['federal_percent'] = f.value.federal_share / 100;
      h1_obj['non_federal_percent'] = f.value.nonfederal_share / 100;
      if (f.value.applied_activity1) {
        h1_obj['administrative'] = true;
      }
      if (f.value.applied_activity2) {
        h1_obj['generic_voter_drive'] = true;
      }
      if (f.value.applied_activity3) {
        h1_obj['public_communications'] = true;
      }
    } else {
      if (f.value.h1_election_year_options === '1') {
        h1_obj['federal_percent'] = '0.28';
        h1_obj['non_federal_percent'] = '0.72';
        h1_obj['presidential_only'] = true;
      } else if (f.value.h1_election_year_options === '2') {
        h1_obj['federal_percent'] = '0.36';
        h1_obj['non_federal_percent'] = '0.64';
        h1_obj['presidential_and_senate'] = true;
      } else if (f.value.h1_election_year_options === '3') {
        h1_obj['federal_percent'] = '0.21';
        h1_obj['non_federal_percent'] = '0.79';
        h1_obj['senate_only'] = true;
      } else if (f.value.h1_election_year_options === '4') {
        h1_obj['federal_percent'] = '0.15';
        h1_obj['non_federal_percent'] = '0.85';
        h1_obj['non_pres_and_non_senate'] = true;
      }
    }
   
    this._http.post(url, JSON.stringify(h1_obj), {
      headers: httpOptions
    }).subscribe(
      res => {
        console.log(res);
        f.value.message = 'h1 saved.'
        f.reset();
      });
  }

  public handleFedShareFieldKeyup(e, f: NgForm) {
    if(e.target.value <= 100) {
      f.controls.nonfederal_share.setValue(100 - e.target.value);
    }else {
      f.controls.nonfederal_share.setValue(0);
    }
  }

  public handleNonFedShareFieldKeyup(e, f: NgForm) {
    if(e.target.value <= 100) {
      f.controls.federal_share.setValue(100 - e.target.value);
    }else {
      f.controls.federal_share.setValue(0);
    }
  }

}
