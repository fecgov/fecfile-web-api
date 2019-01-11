import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { forkJoin, of, interval } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'dynamic-forms',
  templateUrl: './dynamic-forms.component.html',
  styleUrls: ['./dynamic-forms.component.scss'],
  providers: [NgbTooltipConfig],
  encapsulation: ViewEncapsulation.None
})
export class DynamicFormsComponent implements OnInit {

  public currentStep: string = '';
  public formOptionsVisible: boolean = false;
  public frmOption: FormGroup;
  public loadingSteps: boolean = true;
  public loadingCategories: boolean = true;
  public loadingSearchField: boolean = true;
  public loadingCashOnHand: boolean = true;
  public optionFailed: boolean = false;
  public steps: any = {};
  public sidebarLinks: any = {};
  public selectedOptions: any = [];
  public searchField: any = {};
  public cashOnHand: any = {};

  constructor(
  	private _http: HttpClient,
    private _fb: FormBuilder,
    private _config: NgbTooltipConfig
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

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

    this._http.get('http://localhost:3000/cashOnHand')
        .subscribe(resp => {
            this.cashOnHand = resp;

            this.loadingCashOnHand = false;
        });

    this.frmOption = this._fb.group({
      optionRadio: ['', Validators.required]
    });


  }

  /**
   * Get's message from child components.
   *
   * @param      {Object}  e       The event object.
   */
  public onNotify(e): void {
    this.selectedOptions = e.additionalOptions;

    if (e.additionalOptions.length) {
      this.formOptionsVisible = true;
    } else {
      this.formOptionsVisible = false;
    }
  }

  /**
   * Validates the form on submit.
   *
   * @return     {Boolean}  A boolean indicating weather or not the form can be submitted.
   */
  public doValidateOption(): boolean {
    if (this.frmOption.invalid) {
      this.optionFailed = true;
      return false;
    } else {
      this.optionFailed = false;
      return true;
    }
  }

  /**
   * Updates the status of any form erros when a radio button is clicked.
   *
   * @param      {Object}  e       The event object.
   */
  public updateStatus(e): void {
    if (e.target.checked) {
      this.optionFailed = false;
    } else {
      this.optionFailed = true;
    }
  }
}
