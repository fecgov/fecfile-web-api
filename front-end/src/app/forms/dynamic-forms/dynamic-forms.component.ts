import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { forkJoin, of, interval } from 'rxjs';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'dynamic-forms',
  templateUrl: './dynamic-forms.component.html',
  styleUrls: ['./dynamic-forms.component.scss'],
  encapsulation: ViewEncapsulation.None
})
export class DynamicFormsComponent implements OnInit {

  public currentStep: string = '';
  public loadingSteps: boolean = true;
  public loadingCategories: boolean = true;
  public loadingSearchField: boolean = true;
  public steps: any = {};
  public sidebarLinks: any = {};
  public selectedOptions: any = [];
  public searchField: any = {};

  constructor(
  	private _http: HttpClient
  ) { }

  ngOnInit(): void {

	  this._http.get('http://localhost:3000/steps')
	      .subscribe(resp => {
	          this.steps = resp;

            this.loadingSteps = false;
	      });

    this._http.get('http://localhost:3000/transaction-categories')
        .subscribe(resp => {
            this.sidebarLinks = resp;

            this.loadingCategories = false;
        });

    this._http.get('http://localhost:3000/transaction-search-field')
        .subscribe(resp => {
            this.searchField = resp;

            this.loadingSearchField = false;
        });
  }

  /**
   * Get's message from child components.
   *
   * @param      {Object}  e       The event object.
   */
  public onNotify(e): void {
    console.log('onNotify: ');
    console.log('e: ', e);
    this.selectedOptions = e.additionalOptions;
  }
}
