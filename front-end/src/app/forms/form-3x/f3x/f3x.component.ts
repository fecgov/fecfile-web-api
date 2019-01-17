import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormGroup, NgForm, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { forkJoin, of, interval } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { NgbTooltipConfig } from '@ng-bootstrap/ng-bootstrap';
import { FormsService } from '../../../shared/services/FormsService/forms.service';
import { form3x_data } from '../../../shared/interfaces/FormsService/FormsService';

@Component({
  selector: 'app-f3x',
  templateUrl: './f3x.component.html',
  styleUrls: ['./f3x.component.scss'],
  providers: [NgbTooltipConfig],
  encapsulation: ViewEncapsulation.None
})
export class F3xComponent implements OnInit {

  public currentStep: string = 'step_1';
  public step: string = '';
  public formOptionsVisible: boolean = false;
  public frmOption: FormGroup;
  public loadingData: boolean = true;
  public steps: any = {};
  public sidebarLinks: any = {};
  public selectedOptions: any = [];
  public searchField: any = {};
  public cashOnHand: any = {};

  private _form_type: string = '';

  constructor(
    private _formService: FormsService,
    private _http: HttpClient,
    private _fb: FormBuilder,
    private _config: NgbTooltipConfig,
    private _activatedRoute: ActivatedRoute,
  ) {
    this._config.placement = 'right';
    this._config.triggers = 'click';
  }

  ngOnInit(): void {
    this._form_type = this._activatedRoute.snapshot.paramMap.get('form_id');

    this._formService
      .getTransactionCategories()
      .subscribe(res => {
        console.log('resp: ', res);

        this.sidebarLinks = res.data.transactionCategories;

        this.searchField = res.data.transactionSearchField;

        this.step = this.currentStep;

        let formSavedObj: any = {
          'saved': false
        };

        if(localStorage.getItem(`form_${this._form_type}_saved`) === null) {
          localStorage.setItem(`form_${this._form_type}_saved`, JSON.stringify(formSavedObj));
        }

        this.loadingData = false;
      });
  }

  /**
   * Get's message from child components.
   *
   * @param      {Object}  e       The event object.
   */
  public onNotify(e): void {
    // console.log('onNotify: ');

    if (e.additionalOptions.length) {
      this.selectedOptions = e.additionalOptions;
      this.formOptionsVisible = true;
    } else {
      this.selectedOptions = null;
      this.formOptionsVisible = false;
    }
    // if (this.selectedOptions !== null) {
    //   console.log('this.selectedOptions: ', this.selectedOptions);
    // }
  }
}
