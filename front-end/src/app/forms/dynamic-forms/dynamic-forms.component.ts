import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'dynamic-forms',
  templateUrl: './dynamic-forms.component.html',
  styleUrls: ['./dynamic-forms.component.scss']
})
export class DynamicFormsComponent implements OnInit {

  public currentStep: string = '';
  public loading: boolean = true;
  public steps: any = {};
  public sidebarLinks: any = {};

  constructor(
  	private _http: HttpClient
  ) { }

  ngOnInit(): void {
	  this._http.get('http://localhost:3000/steps')
	      .subscribe(resp => {
	          this.steps = resp;
	      });

    this._http.get('http://localhost:3000/transaction-categories')
        .subscribe(resp => {
            this.sidebarLinks = resp;

            this.loading = false;
        });
  }
}
